#    Copyright (c) 2015 Telefonica I+D
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

import os
import tempfile

import mock
from oslo_serialization import base64
import yaml as yamllib

from murano.dsl import murano_object
from murano.dsl import murano_type
from murano.dsl import object_store
from murano.engine.system import agent
from murano.engine.system import resource_manager
from murano.tests.unit import base


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
