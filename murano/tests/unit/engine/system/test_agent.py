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

import mock
import os

import yaml as yamllib

from murano.dsl import murano_class
from murano.dsl import object_store
import murano.engine.system.agent as agent
import murano.engine.system.resource_manager as resource
from murano.tests.unit import base


class TestExecutionPlan(base.MuranoTestCase):
    def setUp(self):
        super(TestExecutionPlan, self).setUp()
        if hasattr(yamllib, 'CSafeLoader'):
            self.yaml_loader = yamllib.CSafeLoader
        else:
            self.yaml_loader = yamllib.SafeLoader

        self.mock_murano_class = mock.Mock(spec=murano_class.MuranoClass)
        self.mock_murano_class.name = 'io.murano.system.Agent'
        self.mock_murano_class.parents = []
        self.mock_object_store = mock.Mock(spec=object_store.ObjectStore)
        self.agent = agent.Agent(self.mock_murano_class, None,
                                 self.mock_object_store, None)
        self.resources = mock.Mock(spec=resource.ResourceManager)
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
        template = self.agent.buildExecutionPlan(template, self.resources)
        self.assertEqual(template, self._get_application())

    def test_execution_plan_v2_chef_type(self):
        template = yamllib.load(
            self._read('chef.template'),
            Loader=self.yaml_loader)
        template = self.agent.buildExecutionPlan(template, self.resources)
        self.assertEqual(template, self._get_chef())

    def test_execution_plan_v2_telnet_application(self):
        template = yamllib.load(
            self._read('DeployTelnet.template'),
            Loader=self.yaml_loader)
        template = self.agent.buildExecutionPlan(template, self.resources)
        self.assertEqual(template, self._get_telnet_application())

    def test_execution_plan_v2_tomcat_application(self):
        template = yamllib.load(
            self._read('DeployTomcat.template'),
            Loader=self.yaml_loader)
        template = self.agent.buildExecutionPlan(template, self.resources)

    def test_execution_plan_v2_app_without_files(self):
        template = yamllib.load(
            self._read('application_without_files.template'),
            Loader=self.yaml_loader)
        template = self.agent.buildExecutionPlan(template, self.resources)
        self.assertEqual(template, self._get_app_without_files())

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

    def _stub_uuid(self, values=[]):
        class FakeUUID(object):
            def __init__(self, v):
                self.hex = v

        mock_uuid4 = mock.patch('uuid.uuid4').start()
        mock_uuid4.side_effect = [FakeUUID(v) for v in values]
        return mock_uuid4
