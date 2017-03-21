# Copyright (c) 2016 AT&T inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import errno
import eventlet
import mock
import socket
import webob

from oslo_config import cfg
from xml.dom import minidom

from murano.common import exceptions
from murano.common.i18n import _
from murano.common import wsgi
from murano.tests.unit import base

CONF = cfg.CONF


class TestServiceBrokerResponseSerializer(base.MuranoTestCase):

    def test_service_broker_response_serializer(self):
        self.sbrs = wsgi.ServiceBrokerResponseSerializer()
        result = self.sbrs.serialize("test_response", "application/json")
        self.assertEqual(200, result.status_code)

        response = webob.Response("test_body")
        response.data = "test_data"
        result = self.sbrs.serialize(response, "application/json")
        self.assertEqual(200, result.status_code)


class TestResponseSerializer(base.MuranoTestCase):

    def test_response_serializer(self):
        self.response_serializer = wsgi.ResponseSerializer(None)
        self.assertRaises(exceptions.UnsupportedContentType,
                          self.response_serializer.get_body_serializer,
                          "not_valid")


class TestRequestDeserializer(base.MuranoTestCase):

    def test_request_deserializer_deserialize_body(self):
        self.request_deserializer = wsgi.RequestDeserializer()
        request = mock.Mock()
        request.get_content_type.side_effect = (
            exceptions.UnsupportedContentType
        )
        request.body = "body"
        self.assertRaises(exceptions.UnsupportedContentType,
                          self.request_deserializer.deserialize_body,
                          request, "act")

        request.get_content_type.side_effect = None
        request.get_content_type.return_value = None
        result = self.request_deserializer.deserialize_body(request, "act")
        self.assertEqual({}, result)

        request.get_content_type.return_value = ""
        self.assertRaises(exceptions.UnsupportedContentType,
                          self.request_deserializer.deserialize_body,
                          request, "act")

    def test_request_deserializer_get_action_args(self):
        self.request_deserializer = wsgi.RequestDeserializer()
        request_environment = []
        result = self.request_deserializer.get_action_args(request_environment)
        self.assertEqual({}, result)

        request_environment = {'wsgiorg.routing_args': ["", {}]}
        result = self.request_deserializer.get_action_args(request_environment)
        self.assertEqual({}, result)


class TestService(base.MuranoTestCase):

    def setUp(self):
        super(TestService, self).setUp()
        # Greatly speed up the time it takes to run the tests that call
        # wsgi._get_socket below: retry_until will be set to 31, the 1st
        # iteration of the while loop will execute because it will evaluate to
        # 30 < 31, but 2nd one will not because it will evaluate to 31 < 31.
        self.mock_time = mock.patch.object(
            wsgi, 'time', **{'time.side_effect': [1, 30, 31]}).start()
        self.addCleanup(mock.patch.stopall)

    @mock.patch("murano.common.wsgi.socket")
    def test_service_get_socket(self, socket):
        self.service = wsgi.Service(None, 1)
        new_socket = self.service._get_socket(None, None, None)
        self.assertIsInstance(new_socket, eventlet.greenio.base.GreenSocket)

        self.mock_time.time.side_effect = [1, 30, 31]
        socket.TCP_KEEPIDLE = True
        new_socket_2 = self.service._get_socket(None, None, None)
        self.assertIsInstance(new_socket_2, eventlet.greenio.base.GreenSocket)

    @mock.patch("murano.common.wsgi.socket")
    @mock.patch("murano.common.wsgi.sslutils")
    def test_service_get_socket_sslutils_enabled(self, sslutils, mock_socket):
        self.service = wsgi.Service(None, 1)
        new_socket = self.service._get_socket(None, None, None)
        self.assertIsNotNone(new_socket)

    @mock.patch("murano.common.wsgi.socket")
    @mock.patch("murano.common.wsgi.eventlet")
    def test_service_get_socket_no_bind(self, eventlet, mock_socket):
        self.service = wsgi.Service(None, 1)
        eventlet.listen.return_value = None
        self.assertRaises(RuntimeError, self.service._get_socket,
                          None, None, None)

    @mock.patch("murano.common.wsgi.socket")
    @mock.patch("murano.common.wsgi.eventlet")
    def test_service_get_socket_os_error(self, eventlet, mock_socket):
        mock_socket.error = socket.error
        self.service = wsgi.Service(None, 1)
        sock_err = socket.error(1)
        eventlet.listen.side_effect = sock_err
        self.assertRaises(socket.error, self.service._get_socket,
                          None, None, None)

    @mock.patch("murano.common.wsgi.socket")
    @mock.patch("murano.common.wsgi.eventlet")
    def test_service_get_socket_socket_error_EADDRINUSE(self, eventlet,
                                                        mock_socket):
        mock_socket.error = socket.error
        self.service = wsgi.Service(None, 1)
        sock_err = socket.error(errno.EADDRINUSE)
        eventlet.listen.side_effect = sock_err
        self.assertRaises(RuntimeError, self.service._get_socket,
                          None, None, None)

    @mock.patch("murano.common.wsgi.eventlet")
    def test_service_start(self, eventlet):
        self.service = wsgi.Service(None, 1)
        self.service.start()
        self.assertTrue(eventlet.spawn.called)

    def test_service_stop(self):
        self.service = wsgi.Service(None, 1)
        self.service.greenthread = mock.Mock()
        self.service.stop()
        self.assertTrue(self.service.greenthread.kill.called)

    def test_service_properties(self):
        self.service = wsgi.Service(None, 1)
        self.service._socket = mock.Mock()
        self.service._socket.getsockname.return_value = ["host", "port"]
        host = self.service.host
        port = self.service.port
        self.assertEqual("host", host)
        self.assertEqual("port", port)

    @mock.patch("murano.common.wsgi.logging")
    def test_service_reset(self, logging):
        self.service = wsgi.Service(None, 1)
        self.service.reset()
        self.assertTrue(logging.setup.called)

    @mock.patch("murano.common.wsgi.eventlet")
    def test_service_run(self, eventlet):
        self.service = wsgi.Service(None, 1)
        self.service._run(None, None)
        self.assertTrue(eventlet.wsgi.server.called)

    def test_backlog_prop(self):
        service = wsgi.Service(None, None)
        service._backlog = mock.sentinel.backlog
        self.assertEqual(mock.sentinel.backlog, service.backlog)


class TestMiddleware(base.MuranoTestCase):

    def test_middleware_call(self):
        self.middleware = wsgi.Middleware(None)
        mock_request = mock.Mock()
        mock_request.get_response.return_value = "a response"
        self.assertEqual("a response", self.middleware(mock_request))

    def test_call_with_response(self):
        middleware = wsgi.Middleware(None)
        middleware.process_request = mock.Mock(return_value=mock.sentinel.resp)

        resp = middleware(mock.sentinel.req)

        self.assertEqual(mock.sentinel.resp, resp)
        middleware.process_request.assert_called_once_with(mock.sentinel.req)


class TestDebug(base.MuranoTestCase):

    def test_debug_call(self):
        self.debug = wsgi.Debug(None)
        mock_request = mock.Mock()
        mock_request.environ = {"one": 1, "two": 2}

        mock_response = mock.Mock()
        mock_response.headers = {"one": 1, "two": 2}
        mock_request.get_response.return_value = mock_response

        self.assertEqual(mock_response, self.debug(mock_request))

    @mock.patch('sys.stdout')
    def test_print_generator(self, mock_stdout):
        for x in wsgi.Debug.print_generator(['foo', 'bar', 'baz']):
            pass
        mock_stdout.write.assert_has_calls([
            mock.call('**************************************** BODY'),
            mock.call('\n'),
            mock.call('foo'),
            mock.call('bar'),
            mock.call('baz'),
            mock.call(''),
            mock.call('\n')
        ])


class TestRequest(base.MuranoTestCase):

    @mock.patch.object(wsgi.webob.BaseRequest, 'path',
                       **{'rsplit.return_value': ['foo.bar', 'baz']})
    def test_best_match_content_type_with_multi_part_path(self, mock_path):
        request = wsgi.Request({})
        supported_content_types = ['application/baz']
        result = request.best_match_content_type(None, supported_content_types)
        self.assertEqual('application/baz', result)


class TestResource(base.MuranoTestCase):

    def test_resource_call_exceptions(self):
        self.resource = wsgi.Resource(None)
        self.resource.deserialize_request = mock.Mock()
        self.resource.deserialize_request.side_effect = (
            exceptions.UnsupportedContentType
        )
        mock_request = mock.Mock()
        mock_request.headers = {}
        result = self.resource(mock_request)
        self.assertEqual(415, result.status_code)

        self.resource.deserialize_request.side_effect = (
            exceptions.MalformedRequestBody
        )
        result = self.resource(mock_request)
        self.assertEqual(400, result.status_code)

        self.resource.deserialize_request.side_effect = None
        self.resource.deserialize_request.return_value = ["", {"k": "v"}, ""]
        self.resource.execute_action = mock.Mock()
        self.resource.serialize_response = mock.Mock()
        self.resource.serialize_response.side_effect = Exception

        result = self.resource(mock_request)
        self.assertIsNotNone(result)

    def test_get_action_args(self):
        self.resource = wsgi.Resource(None)
        result = self.resource.get_action_args(None)
        self.assertEqual({}, result)

        request_environment = {'wsgiorg.routing_args': ["arg_0", {"k": "v"}]}
        result = self.resource.get_action_args(request_environment)
        self.assertEqual({"k": "v"}, result)

    def test_dispatch_except_attribute_error(self):
        mock_obj = mock.Mock(spec=wsgi.Resource)
        setattr(mock_obj, 'default',
                mock.Mock(return_value=mock.sentinel.ret_value))

        resource = wsgi.Resource(None)
        result = resource.dispatch(mock_obj, 'invalid_action')

        self.assertEqual(mock.sentinel.ret_value, result)
        mock_obj.default.assert_called_once_with()


class TestActionDispatcher(base.MuranoTestCase):

    def test_default(self):
        action_dispatcher = wsgi.ActionDispatcher()
        self.assertRaises(NotImplementedError, action_dispatcher.default, None)


class TestDictSerializer(base.MuranoTestCase):

    def test_default(self):
        dict_serializer = wsgi.DictSerializer()
        self.assertEqual("", dict_serializer.default(None))


class TestXMLDictSerializer(base.MuranoTestCase):

    def test_router_dispatch_not_found(self):
        self.router = wsgi.Router(None)
        req = mock.Mock()
        req.environ = {'wsgiorg.routing_args': [False, False]}
        response = self.router._dispatch(req)
        self.assertIsInstance(response, webob.exc.HTTPNotFound)

    def test_XML_Dict_Serializer_default_string(self):
        self.serializer = wsgi.XMLDictSerializer()
        actual_xml = self.serializer.default({"XML Root": "some data"})
        expected_xml = b'<XML Root>some data</XML Root>\n'
        self.assertEqual(expected_xml, actual_xml)

    def test_XML_Dict_Serializer_node_dict(self):
        self.serializer = wsgi.XMLDictSerializer()
        doc = minidom.Document()
        metadata = mock.Mock()
        metadata.get.return_value = {"node": {"item_name": "name",
                                              "item_key": "key"}}
        nodename = "node"
        data = {"data_key": "data_value"}
        result = self.serializer._to_xml_node(doc, metadata, nodename, data)
        self.assertEqual('<name key="data_key">data_value</name>',
                         result.childNodes[0].toxml())

        mock_get_nodename = mock.Mock()
        mock_get_nodename.get.return_vale = "k"
        metadata.get.return_value = {"k": "v"}
        nodename = "node"
        data = {"data_key": "data_value"}
        result = self.serializer._to_xml_node(doc, metadata, nodename, data)
        self.assertEqual("node", result.nodeName)

        metadata.get.return_value = {}
        nodename = "node"
        data = {"data_key": "data_value"}
        result = self.serializer._to_xml_node(doc, metadata, nodename, data)
        self.assertEqual('<data_key>data_value</data_key>',
                         result.childNodes[0].toxml())

    def test_XML_Dict_Serializer_node_list(self):
        self.serializer = wsgi.XMLDictSerializer()
        doc = minidom.Document()
        metadata = mock.Mock()
        metadata.get.return_value = {"node": {"item_name": "name",
                                              "item_key": "key"}}
        nodename = "node"
        data = ["data_1", "data_2", "data_3"]
        result = self.serializer._to_xml_node(doc, metadata, nodename, data)
        self.assertEqual('<name key="data_1"/>', result.childNodes[0].toxml())

        nodename = "not_node"
        data = ["data_1", "data_2", "data_3"]
        result = self.serializer._to_xml_node(doc, metadata, nodename, data)
        self.assertEqual(3, len(result.childNodes))

        nodename = "nodes"
        data = ["data_1", "data_2", "data_3"]
        result = self.serializer._to_xml_node(doc, metadata, nodename, data)
        self.assertEqual(3, len(result.childNodes))

    def test_XML_Dict_Serializer_create_link_nodes(self):
        self.serializer = wsgi.XMLDictSerializer()
        xml_doc = minidom.Document()
        links = [{"rel": "rel", "href": "href", "type": "type"}]
        link_nodes = self.serializer._create_link_nodes(xml_doc, links)
        self.assertEqual('<atom:link href="href" rel="rel" type="type"/>',
                         link_nodes[0].toxml())

    def test_add_xmlns(self):
        xml_dict_serializer = wsgi.XMLDictSerializer()
        xml_dict_serializer.xmlns = mock.sentinel.xmlns
        mock_node = mock.Mock()

        xml_dict_serializer._add_xmlns(mock_node, has_atom=False)
        mock_node.setAttribute.assert_called_once_with(
            'xmlns', mock.sentinel.xmlns)

        mock_node.reset_mock()
        xml_dict_serializer._add_xmlns(mock_node, has_atom=True)
        mock_node.setAttribute.assert_has_calls([
            mock.call('xmlns', mock.sentinel.xmlns),
            mock.call('xmlns:atom', "http://www.w3.org/2005/Atom")
        ])


class TestTextDeserializer(base.MuranoTestCase):

    def test_default(self):
        text_deserializer = wsgi.TextDeserializer()
        self.assertEqual({}, text_deserializer.default(None))


class TestJSONDeserializer(base.MuranoTestCase):

    def test_from_json_except_value_error(self):
        json_deserializer = wsgi.JSONDeserializer()
        e = self.assertRaises(exceptions.MalformedRequestBody,
                              json_deserializer._from_json,
                              "throw value error")
        self.assertIn('cannot understand JSON', str(e))


class TestJSONPatchDeserializer(base.MuranoTestCase):

    def test_from_json_patch_except_value_error(self):
        json_patch_deserializer = wsgi.JSONPatchDeserializer()
        e = self.assertRaises(exceptions.MalformedRequestBody,
                              json_patch_deserializer._from_json_patch,
                              "throw value error")
        self.assertIn('cannot understand JSON', str(e))

    def test_validate_allowed_methods_except_http_forbidden(self):
        json_patch_deserializer = wsgi.JSONPatchDeserializer()
        json_patch_deserializer.allowed_operations = mock.Mock(
            spec_set=wsgi.JSONPatchDeserializer.allowed_operations,
            **{'get.return_value': None}
        )

        e = self.assertRaises(
            webob.exc.HTTPForbidden,
            json_patch_deserializer._validate_allowed_methods,
            {'op': 'foo_op', 'path': 'foo_path'}, allow_unknown_path=False)
        self.assertEqual("Attribute 'f/o/o/_/p/a/t/h' is invalid", str(e))

    def test_validate_json_pointer(self):
        json_patch_deserializer = wsgi.JSONPatchDeserializer()
        expected_exception = webob.exc.HTTPBadRequest
        bad_pointers = ['pointer', '/ /\n/', '//', '// ', '/~2']

        for pointer in bad_pointers:
            self.assertRaises(expected_exception,
                              json_patch_deserializer._validate_json_pointer,
                              pointer)

    @mock.patch.object(wsgi, 'jsonschema', autospec=True)
    def test_validate_schema_cannot_validate(self, mock_jsonschema):
        json_patch_deserializer = wsgi.JSONPatchDeserializer()
        json_patch_deserializer.schema = {'type': 'array'}
        test_change = {'path': ['foo_path'], 'value': 'foo_value'}
        # Assert that jsonschema validation was not performed because
        # can_validate = False.
        json_patch_deserializer._validate_schema(test_change)
        self.assertFalse(mock_jsonschema.validate.called)

        mock_jsonschema.validate.reset_mock()
        json_patch_deserializer = wsgi.JSONPatchDeserializer()
        json_patch_deserializer.schema = {'type': 'object'}
        json_patch_deserializer._validate_schema(test_change)
        self.assertFalse(mock_jsonschema.validate.called)


class TestMuranoPackageJSONPatchDeserializer(base.MuranoTestCase):

    def test_validate_path(self):
        patch_deserializer = wsgi.MuranoPackageJSONPatchDeserializer()
        e = self.assertRaises(webob.exc.HTTPBadRequest,
                              patch_deserializer._validate_path,
                              ['foo_path', 'bar_path'])
        self.assertEqual(_('Nested paths are not allowed'), str(e))


class TestXMLDeserializer(base.MuranoTestCase):

    def test_XMLDeserializer_from_xml(self):
        self.deserializer = wsgi.XMLDeserializer()
        datastring = "<XML>HELLO</XML>"
        request = mock.Mock()
        request.body = datastring
        result = self.deserializer._from_xml(request)
        self.assertEqual({'XML': 'HELLO'}, result)

        datastring = "<NOT XML><NOT XML>"
        request.body = datastring
        self.assertRaises(exceptions.MalformedRequestBody,
                          self.deserializer._from_xml, request)
        datastring = "<XML><XML1>HELLO</XML1></XML>"
        request.body = datastring
        result = self.deserializer._from_xml(request)
        self.assertEqual({'XML': {'XML1': 'HELLO'}}, result)

        datastring = "<XML><XML1><XML2>HELLO</XML2></XML1></XML>"
        request.body = datastring
        result = self.deserializer._from_xml(request)
        self.assertEqual({'XML': {'XML1': {'XML2': 'HELLO'}}}, result)

    def test_XMLDeserializer_default(self):
        self.deserializer = wsgi.XMLDeserializer()
        datastring = "<XML>HELLO</XML>"
        request = mock.Mock()
        request.body = datastring

        result = self.deserializer.default(request)
        self.assertEqual({'body': {'XML': 'HELLO'}}, result)

    def test_XMLDeserializer_find_first_child_named(self):
        self.deserializer = wsgi.XMLDeserializer()
        parent = mock.Mock()
        mock_child = mock.Mock()
        mock_child.nodeName = "name"
        parent.childNodes = [mock_child]
        result = self.deserializer.find_first_child_named(parent, "name")
        self.assertIsNotNone(result)

        parent.childNodes = []
        result = self.deserializer.find_first_child_named(parent, "name")
        self.assertIsNone(result)

        mock_child.nodeName = "other_name"
        parent.childNodes = [mock_child]
        result = self.deserializer.find_first_child_named(parent, "name")
        self.assertIsNone(result)

    def test_XMLDeserializer_extract_text(self):
        self.deserializer = wsgi.XMLDeserializer()
        mock_node = mock.Mock()
        mock_child = mock.Mock()
        mock_child.nodeType = mock_child.TEXT_NODE
        mock_node.childNodes = [mock_child]
        result = self.deserializer.extract_text(mock_node)

        mock_child.nodeType = None
        mock_node.childNodes = [mock_child]
        result = self.deserializer.extract_text(mock_node)
        self.assertEqual("", result)

        mock_node.childNodes = []
        result = self.deserializer.extract_text(mock_node)
        self.assertEqual("", result)

    def test_from_xml_node_all_branches(self):
        mock_grandchild_node = mock.MagicMock(**{
            'nodeName': 'qux',
            'nodeType': mock.sentinel.grandchild_node_type,
            'childNodes': [
                mock.Mock(nodeType=3, nodeValue=mock.sentinel.qux_node)
            ]
        })
        mock_child_node = mock.MagicMock(**{
            'nodeName': mock.sentinel.child_node,
            'attributes.keys.return_value': ['foo', 'bar', 'baz'],
            'attributes.__getitem__.side_effect': [
                mock.Mock(nodeValue=mock.sentinel.foo_node),
                mock.Mock(nodeValue=mock.sentinel.bar_node),
                mock.Mock(nodeValue=mock.sentinel.baz_node)
            ],
            'childNodes': [
                mock_grandchild_node
            ],
            'TEXT_NODE': mock.sentinel.child_node_type
        })
        mock_node = mock.Mock(**{
            'nodeName': mock.sentinel.parent_node,
            'childNodes': [
                mock_child_node
            ]
        })
        listnames = [mock.sentinel.parent_node]

        xml_deserializer = wsgi.XMLDeserializer()
        result = xml_deserializer._from_xml_node(mock_node, listnames)
        expected_result = [{
            'foo': mock.sentinel.foo_node,
            'bar': mock.sentinel.bar_node,
            'baz': mock.sentinel.baz_node,
            'qux': mock.sentinel.qux_node
        }]

        self.assertEqual(1, len(result))
        self.assertEqual(len(expected_result[0]), len(result[0]))
        for key, val in expected_result[0].items():
            self.assertEqual(val, result[0][key])

    def test_find_children_named(self):
        child_node = mock.Mock(nodeName=mock.sentinel.node_name)
        parent_node = mock.Mock(childNodes=[child_node])

        result = []
        xml_deserializer = wsgi.XMLDeserializer()
        for n in xml_deserializer.\
                find_children_named(parent_node, mock.sentinel.node_name):
            result.append(n)

        self.assertEqual(1, len(result))
        self.assertEqual(child_node, result[0])


class TestFormDataDeserializer(base.MuranoTestCase):

    @mock.patch.object(wsgi, 'LOG', autospec=True)
    def test_from_json_except_value_error(self, mock_log):
        data_serializer = wsgi.FormDataDeserializer()
        value = data_serializer._from_json('value error')

        self.assertEqual('value error', value)
        mock_log.debug.assert_called_once_with(
            "Trying to deserialize 'value error' to json")
        mock_log.warning.assert_called_once_with(
            'Unable to deserialize to json, using raw text')
