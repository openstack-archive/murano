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
from murano.common import wsgi
from murano.tests.unit import base

CONF = cfg.CONF


class WsgiTest(base.MuranoTestCase):
    @mock.patch("murano.common.wsgi.socket")
    def test_service_get_socket(self, socket):
        self.service = wsgi.Service(None, 1)
        new_socket = self.service._get_socket(None, None, None)
        self.assertIsInstance(new_socket, eventlet.greenio.base.GreenSocket)
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

    @mock.patch("murano.common.wsgi.time")
    @mock.patch("murano.common.wsgi.socket")
    @mock.patch("murano.common.wsgi.eventlet")
    def test_service_get_socket_os_error(self, eventlet, mock_socket, time):
        mock_socket.error = socket.error
        self.service = wsgi.Service(None, 1)
        sock_err = socket.error(1)
        eventlet.listen.side_effect = sock_err

        # Speed up unit test in case of RuntimeError.
        time.time.side_effect = [1, 30, 31]
        self.assertRaises(socket.error, self.service._get_socket,
                          None, None, None)

    @mock.patch("murano.common.wsgi.time")
    @mock.patch("murano.common.wsgi.socket")
    @mock.patch("murano.common.wsgi.eventlet")
    def test_service_get_socket_socket_error_EADDRINUSE(self, eventlet,
                                                        mock_socket, time):
        mock_socket.error = socket.error
        self.service = wsgi.Service(None, 1)
        sock_err = socket.error(errno.EADDRINUSE)

        # Speed up unit test in case of RuntimeError.
        time.time.side_effect = [1, 30, 31]
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

    def test_middleware_call(self):
        self.middleware = wsgi.Middleware(None)
        mock_request = mock.Mock()
        mock_request.get_response.return_value = "a response"
        self.assertEqual("a response", self.middleware(mock_request))

    def test_debug_call(self):
        self.debug = wsgi.Debug(None)
        mock_request = mock.Mock()
        mock_request.environ = {"one": 1, "two": 2}

        mock_response = mock.Mock()
        mock_response.headers = {"one": 1, "two": 2}
        mock_request.get_response.return_value = mock_response

        self.assertEqual(mock_response, self.debug(mock_request))

    def test_router_dispatch_not_found(self):
        self.router = wsgi.Router(None)
        req = mock.Mock()
        req.environ = {'wsgiorg.routing_args': [False, False]}
        response = self.router._dispatch(req)
        self.assertIsInstance(response, webob.exc.HTTPNotFound)

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

    def test_service_broker_response_serializer(self):
        self.sbrs = wsgi.ServiceBrokerResponseSerializer()
        result = self.sbrs.serialize("test_response", "application/json")
        self.assertEqual(200, result.status_code)

        response = webob.Response("test_body")
        response.data = "test_data"
        result = self.sbrs.serialize(response, "application/json")
        self.assertEqual(200, result.status_code)

    def test_response_serializer(self):
        self.response_serializer = wsgi.ResponseSerializer(None)
        self.assertRaises(exceptions.UnsupportedContentType,
                          self.response_serializer.get_body_serializer,
                          "not_valid")

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
