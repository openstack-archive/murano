#    Copyright (c) 2015 Telefonica I+D
#    Copyright (c) 2016 AT&T Corp
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

import copy
import datetime
import json
import os
import tempfile

import mock
from oslo_serialization import base64
import yaml as yamllib

from murano.common import exceptions
from murano.dsl import dsl
from murano.dsl import murano_object
from murano.dsl import murano_type
from murano.dsl import object_store
from murano.engine.system import agent
from murano.engine.system import resource_manager
from murano.tests.unit import base


class TestAgent(base.MuranoTestCase):
    def setUp(self):
        super(TestAgent, self).setUp()
        if hasattr(yamllib, 'CSafeLoader'):
            self.yaml_loader = yamllib.CSafeLoader
        else:
            self.yaml_loader = yamllib.SafeLoader

        self.override_config('disable_murano_agent', False, group='engine')

        mock_host = mock.MagicMock()
        mock_host.id = '1234'
        mock_host.find_owner = lambda *args, **kwargs: mock_host
        mock_host().getRegion.return_value = mock.MagicMock(
            __class__=dsl.MuranoObjectInterface)
        self.rabbit_mq_settings = {
            'agentRabbitMq': {'login': 'test_login',
                              'password': 'test_password',
                              'host': 'test_host',
                              'port': 123,
                              'virtual_host': 'test_virtual_host'}
        }
        mock_host().getRegion()().getConfig.return_value =\
            self.rabbit_mq_settings

        self.agent = agent.Agent(mock_host)
        self.resources = mock.Mock(spec=resource_manager.ResourceManager)
        self.resources.string.return_value = 'text'

        self.addCleanup(mock.patch.stopall)

    def _read(self, path):
        execution_plan_dir = os.path.abspath(
            os.path.join(__file__, '../execution_plans/')
        )
        with open(execution_plan_dir + "/" + path) as file:
            return file.read()

    @mock.patch('murano.common.messaging.mqclient.kombu')
    def test_send_creates_queue(self, mock_kombu):
        self.agent.send_raw({})

        # Verify that MQClient was instantiated, by checking whether
        # kombu.Connection was called.
        mock_kombu.Connection.assert_called_with(
            'amqp://{login}:{password}@{host}:{port}/{virtual_host}'.format(
                **self.rabbit_mq_settings['agentRabbitMq']
            ), ssl=None)

        # Verify that client.declare() was called by checking whether kombu
        # functions were called.
        self.assertEqual(1, mock_kombu.Exchange.call_count)
        self.assertEqual(1, mock_kombu.Queue.call_count)

    @mock.patch('murano.engine.system.agent.LOG')
    def test_send_with_murano_agent_disabled(self, mock_log):
        self.override_config('disable_murano_agent', True, group='engine')

        self.assertRaises(exceptions.PolicyViolationException,
                          self.agent.send_raw, {})

    @mock.patch('murano.engine.system.agent.Agent._sign')
    @mock.patch('murano.common.messaging.mqclient.kombu')
    def test_send(self, mock_kombu, mock_sign):
        template = yamllib.load(
            self._read('template_with_files.template'),
            Loader=self.yaml_loader)

        self.agent._queue = 'test_queue'
        mock_sign.return_value = 'SIGNATURE'
        plan = self.agent.build_execution_plan(template, self.resources)
        with mock.patch.object(self.agent, 'build_execution_plan',
                               return_value=plan):
            self.agent.send(template, self.resources)

        self.assertEqual(1, mock_kombu.Producer.call_count)
        mock_kombu.Producer().publish.assert_called_once_with(
            exchange='',
            routing_key='test_queue',
            body=json.dumps(plan),
            message_id=plan['ID'],
            headers={'signature': 'SIGNATURE'}
        )

    @mock.patch('murano.engine.system.agent.eventlet.event.Event')
    @mock.patch('murano.common.messaging.mqclient.kombu')
    def test_is_ready(self, mock_kombu, mock_event):
        v2_result = yamllib.load(
            self._read('application.template'),
            Loader=self.yaml_loader)

        mock_event().wait.side_effect = None
        mock_event().wait.return_value = v2_result

        self.assertTrue(self.agent.is_ready(1))

        mock_event().wait.side_effect = agent.eventlet.Timeout

        self.assertFalse(self.agent.is_ready(1))

    @mock.patch('murano.engine.system.agent.Agent._sign')
    @mock.patch('murano.engine.system.agent.eventlet.event.Event')
    @mock.patch('murano.common.messaging.mqclient.kombu')
    def test_call_with_v1_result(self, mock_kombu, mock_event, mock_sign):
        template = yamllib.load(
            self._read('template_with_files.template'),
            Loader=self.yaml_loader)

        test_v1_result = {
            'FormatVersion': '1.0.0',
            'IsException': False,
            'Result': [
                {
                    'IsException': False,
                    'Result': 'test_result'
                }
            ]
        }

        mock_event().wait.side_effect = None
        mock_event().wait.return_value = test_v1_result
        mock_sign.return_value = 'SIGNATURE'

        self.agent._queue = 'test_queue'
        plan = self.agent.build_execution_plan(template, self.resources)
        mock.patch.object(
            self.agent, 'build_execution_plan', return_value=plan).start()

        result = self.agent.call(template, self.resources, None)
        self.assertIsNotNone(result)
        self.assertEqual('test_result', result)

        self.assertEqual(1, mock_kombu.Producer.call_count)
        mock_kombu.Producer().publish.assert_called_once_with(
            exchange='',
            routing_key='test_queue',
            body=json.dumps(plan),
            message_id=plan['ID'],
            headers={'signature': 'SIGNATURE'}
        )

    @mock.patch('murano.engine.system.agent.Agent._sign')
    @mock.patch('murano.engine.system.agent.eventlet.event.Event')
    @mock.patch('murano.common.messaging.mqclient.kombu')
    def test_call_with_v2_result(self, mock_kombu, mock_event, mock_sign):
        template = yamllib.load(
            self._read('template_with_files.template'),
            Loader=self.yaml_loader)

        v2_result = yamllib.load(
            self._read('application.template'),
            Loader=self.yaml_loader)

        mock_event().wait.side_effect = None
        mock_event().wait.return_value = v2_result
        mock_sign.return_value = 'SIGNATURE'

        self.agent._queue = 'test_queue'
        plan = self.agent.build_execution_plan(template, self.resources)
        mock.patch.object(
            self.agent, 'build_execution_plan', return_value=plan).start()

        result = self.agent.call(template, self.resources, None)
        self.assertIsNotNone(result)
        self.assertEqual(v2_result['Body'], result)

        self.assertEqual(1, mock_kombu.Producer.call_count)
        mock_kombu.Producer().publish.assert_called_once_with(
            exchange='',
            routing_key='test_queue',
            body=json.dumps(plan),
            message_id=plan['ID'],
            headers={'signature': 'SIGNATURE'}
        )

    @mock.patch('murano.engine.system.agent.eventlet.event.Event')
    @mock.patch('murano.common.messaging.mqclient.kombu')
    def test_call_with_no_result(self, mock_kombu, mock_event):
        template = yamllib.load(
            self._read('template_with_files.template'),
            Loader=self.yaml_loader)

        mock_event().wait.side_effect = None
        mock_event().wait.return_value = None

        result = self.agent.call(template, self.resources, None)
        self.assertIsNone(result)

    @mock.patch('murano.engine.system.agent.eventlet.event.Event')
    @mock.patch('murano.common.messaging.mqclient.kombu')
    def test_call_except_timeout(self, mock_kombu, mock_event):
        self.override_config('agent_timeout', 1, group='engine')

        mock_event().wait.side_effect = agent.eventlet.Timeout

        template = yamllib.load(
            self._read('template_with_files.template'),
            Loader=self.yaml_loader)

        expected_error_msg = 'The murano-agent did not respond within 1 '\
                             'seconds'
        with self.assertRaisesRegex(exceptions.TimeoutException,
                                    expected_error_msg):
            self.agent.call(template, self.resources, None)

    @mock.patch('murano.engine.system.agent.datetime')
    def test_process_v1_result_with_error_code(self, mock_datetime):
        now = datetime.datetime.now().isoformat()
        mock_datetime.datetime.now().isoformat.return_value = now

        v1_result = {
            'IsException': True,
            'Result': [
                'Error Type',
                'Error Message',
                'Error Command',
                'Error Details'
            ]
        }

        expected_error = {
            'source': 'execution_plan',
            'command': 'Error Command',
            'details': 'Error Details',
            'message': 'Error Message',
            'type': 'Error Type',
            'timestamp': now
        }

        self.assertTrue(self._are_exceptions_equal(
            agent.AgentException, expected_error,
            self.agent._process_v1_result, v1_result))

        v1_result = {
            'IsException': False,
            'Result': [
                'Error Type',
                'Error Message',
                'Error Command',
                'Error Details',
                {
                    'IsException': True,
                    'Result': [
                        'Nested Error Type',
                        'Nested Error Message',
                        'Nested Error Command',
                        'Nested Error Details'
                    ]
                }
            ]
        }

        expected_error = {
            'source': 'command',
            'command': 'Nested Error Command',
            'details': 'Nested Error Details',
            'message': 'Nested Error Message',
            'type': 'Nested Error Type',
            'timestamp': now
        }

        self.assertTrue(self._are_exceptions_equal(
            agent.AgentException, expected_error,
            self.agent._process_v1_result, v1_result))

    def test_process_v2_result_with_error_code(self):
        v2_result = {
            'Body': {
                'Message': 'Test Error Message',
                'AdditionalInfo': 'Test Additional Info',
                'ExtraAttr': 'Test extra data'
            },
            'FormatVersion': '2.0.0',
            'Name': 'TestApp',
            'ErrorCode': 123,
            'Time': 'Right now'
        }

        expected_error = {
            'errorCode': 123,
            'message': 'Test Error Message',
            'details': 'Test Additional Info',
            'time': 'Right now',
            'extra': {'ExtraAttr': 'Test extra data'}
        }

        self.assertTrue(self._are_exceptions_equal(
            agent.AgentException, expected_error,
            self.agent._process_v2_result, v2_result))

    def _are_exceptions_equal(self, exception, expected_error, function,
                              result):
        """Checks whether expected and returned dict from exception are equal.

        Because casting dicts to strings changes the ordering of the keys,
        manual comparison of the result and expected result is performed.
        """
        try:
            # deepcopy must be performed because _process_v1_result
            # deletes attrs from the original dict passed in.
            self.assertRaises(exception, function, copy.deepcopy(result))
            function(result)
        except exception as e:
            e_string = str(e).replace("'", "\"").replace('None', 'null')
            e_dict = json.loads(e_string)
            self.assertEqual(sorted(expected_error.keys()),
                             sorted(e_dict.keys()))
            for key, val in expected_error.items():
                self.assertEqual(val, e_dict[key])
        except Exception:
            return False
        return True


class TestExecutionPlan(base.MuranoTestCase):
    def setUp(self):
        super(TestExecutionPlan, self).setUp()
        if hasattr(yamllib, 'CSafeLoader'):
            self.yaml_loader = yamllib.CSafeLoader
        else:
            self.yaml_loader = yamllib.SafeLoader

        self.mock_murano_class = mock.Mock(spec=murano_type.MuranoClass)
        self.mock_murano_class.name = 'io.murano.system.Agent'
        self.mock_murano_class.declared_parents = []
        self.mock_object_store = mock.Mock(spec=object_store.ObjectStore)

        object_interface = mock.Mock(spec=murano_object.MuranoObject)
        object_interface.id = '1234'
        object_interface.find_owner = lambda *args, **kwargs: object_interface

        self.agent = agent.Agent(object_interface)
        self.resources = mock.Mock(spec=resource_manager.ResourceManager)
        self.resources.string.return_value = 'text'
        self.uuids = ['ID1', 'ID2', 'ID3', 'ID4']
        self.mock_uuid = self._stub_uuid(self.uuids)
        time_mock = mock.patch('time.time').start()
        time_mock.return_value = 2
        self.addCleanup(mock.patch.stopall)

    def _read(self, path):
        execution_plan_dir = os.path.abspath(
            os.path.join(__file__, '../execution_plans/')
        )
        with open(execution_plan_dir + "/" + path) as file:
            return file.read()

    def test_execution_plan_v2_application_type(self):
        template = yamllib.load(
            self._read('application.template'),
            Loader=self.yaml_loader)
        template = self.agent.build_execution_plan(template, self.resources)
        self.assertEqual(self._get_application(), template)

    def test_execution_plan_v2_chef_type(self):
        template = yamllib.load(
            self._read('chef.template'),
            Loader=self.yaml_loader)
        template = self.agent.build_execution_plan(template, self.resources)
        self.assertEqual(self._get_chef(), template)

    def test_execution_plan_v2_telnet_application(self):
        template = yamllib.load(
            self._read('DeployTelnet.template'),
            Loader=self.yaml_loader)
        template = self.agent.build_execution_plan(template, self.resources)
        self.assertEqual(self._get_telnet_application(), template)

    def test_execution_plan_v2_tomcat_application(self):
        template = yamllib.load(
            self._read('DeployTomcat.template'),
            Loader=self.yaml_loader)
        template = self.agent.build_execution_plan(template, self.resources)

    def test_execution_plan_v2_app_without_files(self):
        template = yamllib.load(
            self._read('application_without_files.template'),
            Loader=self.yaml_loader)
        template = self.agent.build_execution_plan(template, self.resources)
        self.assertEqual(self._get_app_without_files(), template)

    def test_execution_plan_v2_app_with_file_in_template(self):
        template = yamllib.load(
            self._read('template_with_files.template'),
            Loader=self.yaml_loader)
        template = self.agent.build_execution_plan(template, self.resources)
        self.assertEqual(self._get_app_with_files_in_template(), template)

    def _get_application(self):
        return {
            'Action': 'Execute',
            'Body': 'return deploy(args.appName).stdout\n',
            'Files': {
                self.uuids[1]: {
                    'Body': 'text',
                    'BodyType': 'Text',
                    'Name': 'deployTomcat.sh'
                },
                self.uuids[2]: {
                    'Body': 'dGV4dA==\n',
                    'BodyType': 'Base64',
                    'Name': 'installer'
                },
                self.uuids[3]: {
                    'Body': 'dGV4dA==\n',
                    'BodyType': 'Base64',
                    'Name': 'common.sh'
                }
            },
            'FormatVersion': '2.0.0',
            'ID': self.uuids[0],
            'Stamp': 20000,
            'Name': 'Deploy Tomcat',
            'Parameters': {
                'appName': '$appName'
            },
            'Scripts': {
                'deploy': {
                    'EntryPoint': self.uuids[1],
                    'Files': [
                        self.uuids[2],
                        self.uuids[3]
                    ],
                    'Options': {
                        'captureStderr': True,
                        'captureStdout': True
                    },
                    'Type': 'Application',
                    'Version': '1.0.0'
                }
            },
            'Version': '1.0.0'
        }

    def _get_app_with_files_in_template(self):
        return {
            'Action': 'Execute',
            'Body': 'return deploy(args.appName).stdout\n',
            'Files': {
                self.uuids[1]: {
                    'Body': 'text',
                    'BodyType': 'Text',
                    'Name': 'deployTomcat.sh'
                },
                'updateScript': {
                    'Body': 'text',
                    'BodyType': 'Text',
                    'Name': 'updateScript'
                },
            },
            'FormatVersion': '2.0.0',
            'ID': self.uuids[0],
            'Stamp': 20000,
            'Name': 'Deploy Tomcat',
            'Parameters': {
                'appName': '$appName'
            },
            'Scripts': {
                'deploy': {
                    'EntryPoint': self.uuids[1],
                    'Files': [
                        'updateScript'
                    ],
                    'Options': {
                        'captureStderr': True,
                        'captureStdout': True
                    },
                    'Type': 'Application',
                    'Version': '1.0.0'
                }
            },
            'Version': '1.0.0'
        }

    def _get_app_without_files(self):
        return {
            'Action': 'Execute',
            'Body': 'return deploy(args.appName).stdout\n',
            'Files': {
                self.uuids[1]: {
                    'Body': 'text',
                    'BodyType': 'Text',
                    'Name': 'deployTomcat.sh'
                },
            },
            'FormatVersion': '2.0.0',
            'ID': self.uuids[0],
            'Stamp': 20000,
            'Name': 'Deploy Tomcat',
            'Parameters': {
                'appName': '$appName'
            },
            'Scripts': {
                'deploy': {
                    'EntryPoint': self.uuids[1],
                    'Files': [],
                    'Options': {
                        'captureStderr': True,
                        'captureStdout': True
                    },
                    'Type': 'Application',
                    'Version': '1.0.0'
                }
            },
            'Version': '1.0.0'
        }

    def _get_chef(self):
        return {
            'Action': 'Execute',
            'Body': 'return deploy(args.appName).stdout\n',
            'Files': {
                self.uuids[1]: {
                    'Name': 'tomcat.git',
                    'Type': 'Downloadable',
                    'URL': 'https://github.com/tomcat.git'
                },
                self.uuids[2]: {
                    'Name': 'java',
                    'Type': 'Downloadable',
                    'URL': 'https://github.com/java.git'
                },

            },
            'FormatVersion': '2.0.0',
            'ID': self.uuids[0],
            'Stamp': 20000,
            'Name': 'Deploy Chef',
            'Parameters': {
                'appName': '$appName'
            },
            'Scripts': {
                'deploy': {
                    'EntryPoint': 'cookbook/recipe',
                    'Files': [
                        self.uuids[1],
                        self.uuids[2]
                    ],
                    'Options': {
                        'captureStderr': True,
                        'captureStdout': True
                    },
                    'Type': 'Chef',
                    'Version': '1.0.0'
                }
            },
            'Version': '1.0.0'
        }

    def _get_telnet_application(self):
        return {
            'Action': 'Execute',
            'Body': 'return deploy(args.appName).stdout\n',
            'Files': {
                self.uuids[1]: {
                    'Body': 'text',
                    'BodyType': 'Text',
                    'Name': 'deployTelnet.sh'
                },
                self.uuids[2]: {
                    'Body': 'text',
                    'BodyType': 'Text',
                    'Name': 'installer.sh'
                },
                self.uuids[3]: {
                    'Body': 'text',
                    'BodyType': 'Text',
                    'Name': 'common.sh'
                }
            },
            'FormatVersion': '2.0.0',
            'ID': self.uuids[0],
            'Stamp': 20000,
            'Name': 'Deploy Telnet',
            'Parameters': {
                'appName': '$appName'
            },
            'Scripts': {
                'deploy': {
                    'EntryPoint': self.uuids[1],
                    'Files': [
                        self.uuids[2],
                        self.uuids[3]
                    ],
                    'Options': {
                        'captureStderr': True,
                        'captureStdout': True
                    },
                    'Type': 'Application',
                    'Version': '1.0.0'
                }
            },
            'Version': '1.0.0'
        }

    def _stub_uuid(self, values=None):
        class FakeUUID(object):
            def __init__(self, v):
                self.hex = v

        if values is None:
            values = []
        mock_uuid4 = mock.patch('uuid.uuid4').start()
        mock_uuid4.side_effect = [FakeUUID(v) for v in values]
        return mock_uuid4

    @mock.patch('murano.engine.system.resource_manager.ResourceManager'
                '._get_package')
    def test_file_line_endings(self, _get_package):
        class FakeResources(object):
            """Class with only string() method from ResourceManager class"""
            @staticmethod
            def string(name, owner=None, binary=False):
                return resource_manager.ResourceManager.string(
                    receiver=None, name=name, owner=owner, binary=binary)

        # make path equal to provided name inside resources.string()
        package = mock.Mock()
        package.get_resource.side_effect = lambda m: m
        _get_package.return_value = package

        text = b"First line\nSecond line\rThird line\r\nFourth line"
        modified_text = u"First line\nSecond line\nThird line\nFourth line"
        encoded_text = base64.encode_as_text(text) + "\n"
        resources = FakeResources()

        with tempfile.NamedTemporaryFile() as script_file:
            script_file.write(text)
            script_file.file.flush()
            os.fsync(script_file.file.fileno())

            # check that data has been written correctly
            script_file.seek(0)
            file_data = script_file.read()
            self.assertEqual(text, file_data)

            # check resources.string() output
            # text file
            result = resources.string(script_file.name)
            self.assertEqual(modified_text, result)
            # binary file
            result = resources.string(script_file.name, binary=True)
            self.assertEqual(text, result)

            # check _get_body() output
            filename = os.path.basename(script_file.name)
            folder = os.path.dirname(script_file.name)
            # text file
            body = self.agent._get_body(filename, resources, folder)
            self.assertEqual(modified_text, body)
            # binary file
            filename = '<{0}>'.format(filename)
            body = self.agent._get_body(filename, resources, folder)
            self.assertEqual(encoded_text, body)

    def test_queue_name(self):
        self.agent._queue = 'test_queue'
        self.assertEqual(self.agent.queue_name(), self.agent._queue)

    def test_prepare_message(self):
        template = {'test'}
        msg_id = 12345
        msg = self.agent._prepare_message(template, msg_id)
        self.assertEqual(msg.id, msg_id)
        self.assertEqual(msg._body, template)

    def test_execution_plan_v1(self):
        template = yamllib.load(
            self._read('application.template'),
            Loader=self.yaml_loader)
        rtn_template = self.agent._build_v1_execution_plan(template,
                                                           self.resources)
        self.assertEqual(template, rtn_template)

    def test_get_array_item(self):
        array = [1, 2, 3]
        index = 2
        self.assertEqual(array[2], self.agent._get_array_item(array, index))

        index = 3
        self.assertIsNone(self.agent._get_array_item(array, index))

    def test_execution_plan_error(self):
        template = None
        self.assertRaises(ValueError,
                          self.agent.build_execution_plan,
                          template, self.resources)
