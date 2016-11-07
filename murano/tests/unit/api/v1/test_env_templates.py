# Copyright (c) 2015 Telefonica I+D.
# Copyright (c) 2016 AT&T Corp
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from datetime import datetime
import mock

from oslo_config import fixture as config_fixture
from oslo_db import exception as db_exc
from oslo_serialization import jsonutils
from oslo_utils import timeutils

from murano.api.v1 import templates
from murano.db import models
import murano.tests.unit.api.base as tb
import murano.tests.unit.utils as test_utils


class TestEnvTemplateApi(tb.ControllerTest, tb.MuranoApiTestCase):

    def setUp(self):
        super(TestEnvTemplateApi, self).setUp()
        self.controller = templates.Controller()
        self.uuids = ['env_template_id', 'other', 'network_id',
                      'environment_id', 'session_id']
        self.mock_uuid = self._stub_uuid(self.uuids)

    def test_list_empty_env_templates(self):
        """Check that with no templates an empty list is returned."""
        self._set_policy_rules(
            {'list_env_templates': '@'}
        )
        self.expect_policy_check('list_env_templates')

        req = self._get('/templates')
        result = req.get_response(self.api)
        self.assertEqual({'templates': []}, jsonutils.loads(result.body))

    def test_create_env_templates(self):
        """Create an template, test template.show()."""
        self._set_policy_rules(
            {'list_env_templates': '@',
             'create_env_template': '@',
             'show_env_template': '@'}
        )
        self.expect_policy_check('create_env_template')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        expected = {'tenant_id': self.tenant,
                    'id': 'env_template_id',
                    'is_public': False,
                    'name': 'mytemp',
                    'description_text': 'description',
                    'version': 0,
                    'created': datetime.isoformat(fake_now)[:-7],
                    'updated': datetime.isoformat(fake_now)[:-7]}

        body = {'name': 'mytemp', 'description_text': 'description'}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)

        self.assertEqual(expected, jsonutils.loads(result.body))

        # Reset the policy expectation
        self.expect_policy_check('list_env_templates')

        req = self._get('/templates')
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
        self.assertEqual({'templates': [expected]},
                         jsonutils.loads(result.body))

        expected['services'] = []

        self.expect_policy_check('show_env_template',
                                 {'env_template_id': self.uuids[0]})
        req = self._get('/templates/%s' % self.uuids[0])
        result = req.get_response(self.api)
        self.assertEqual(expected, jsonutils.loads(result.body))

    @mock.patch('murano.db.services.environment_templates.EnvTemplateServices.'
                'create')
    def test_create_env_templates_handle_duplicate_exc(self, mock_function):
        """Create an template, test template.show()."""
        self._set_policy_rules(
            {'create_env_template': '@'}
        )
        self.expect_policy_check('create_env_template')
        mock_function.side_effect = db_exc.DBDuplicateEntry

        body = {'name': 'mytemp', 'description_text': 'description'}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(409, result.status_code)

    def test_list_public_env_templates(self):
        """Create an template, test templates.public()."""
        self._set_policy_rules(
            {'create_env_template': '@',
             'list_env_templates': '@'}
        )

        self.expect_policy_check('create_env_template')

        body = {'name': 'mytemp2', 'is_public': True}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertTrue(jsonutils.loads(result.body)['is_public'])

        self.expect_policy_check('list_env_templates')
        req = self._get('/templates', {'is_public': True})

        result = req.get_response(self.api)
        data = jsonutils.loads(result.body)
        self.assertEqual(1, len(data))
        self.assertTrue(data['templates'][0]['is_public'])

    def test_clone_env_templates(self):
        """Create an template, test templates.public()."""
        self._set_policy_rules(
            {'create_env_template': '@',
             'clone_env_template': '@'}
        )

        self.expect_policy_check('create_env_template')
        body = {'name': 'mytemp2', 'is_public': True}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        env_template_id = jsonutils.loads(result.body)['id']
        self.assertTrue(jsonutils.loads(result.body)['is_public'])

        self.expect_policy_check('clone_env_template')
        body = {'name': 'clone', 'is_public': False}
        req = self._post('/templates/%s/clone' % env_template_id,
                         jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertFalse(jsonutils.loads(result.body)['is_public'])
        self.assertEqual('clone', jsonutils.loads(result.body)['name'])

    def test_clone_env_templates_private(self):
        """Create an template, test templates.public()."""
        self._set_policy_rules(
            {'create_env_template': '@',
             'clone_env_template': '@'}
        )

        self.expect_policy_check('create_env_template')
        body = {'name': 'mytemp2', 'is_public': False}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        env_template_id = jsonutils.loads(result.body)['id']
        self.assertFalse(jsonutils.loads(result.body)['is_public'])

        self.expect_policy_check('clone_env_template')
        body = {'name': 'clone', 'is_public': False}
        req = self._post('/templates/%s/clone' % env_template_id,
                         jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(result.status_code, 403)

    @mock.patch('murano.db.services.environment_templates.EnvTemplateServices.'
                'clone')
    def test_clone_env_templates_handle_duplicate_exc(self, mock_function):
        """Test whether clone duplication exception is handled correctly."""
        mock_function.side_effect = db_exc.DBDuplicateEntry

        self._set_policy_rules(
            {'create_env_template': '@',
             'clone_env_template': '@'}
        )

        self.expect_policy_check('create_env_template')
        body = {'name': 'mytemp2', 'is_public': True}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        env_template_id = jsonutils.loads(result.body)['id']

        self.expect_policy_check('clone_env_template')
        body = {'name': 'clone', 'is_public': False}
        req = self._post('/templates/%s/clone' % env_template_id,
                         jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(409, result.status_code)

    def test_list_public_env_templates_default(self):
        """Test listing public templates when there aren't any

        Create a template; test list public with no
        public templates.
        """
        self._set_policy_rules(
            {'create_env_template': '@',
             'list_env_templates': '@'}
        )

        self.expect_policy_check('create_env_template')
        body = {'name': 'mytemp'}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertFalse(jsonutils.loads(result.body)['is_public'])

        self.expect_policy_check('list_env_templates')
        req = self._get('/templates', {'is_public': True})
        result = req.get_response(self.api)

        self.assertFalse(0, len(jsonutils.loads(result.body)))

    def test_list_private_env_templates(self):
        """Test listing private templates

        Create a public template and a private template;
        test list private templates.
        """
        self._set_policy_rules(
            {'create_env_template': '@',
             'list_env_templates': '@'}
        )

        self.expect_policy_check('create_env_template')
        body = {'name': 'mytemp', 'is_public': False}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertFalse(jsonutils.loads(result.body)['is_public'])

        self.expect_policy_check('create_env_template')
        body = {'name': 'mytemp1', 'is_public': True}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertTrue(jsonutils.loads(result.body)['is_public'])

        self.expect_policy_check('list_env_templates')
        req = self._get('/templates', {'is_public': False})
        result = req.get_response(self.api)
        self.assertEqual(1, len(jsonutils.loads(result.body)['templates']))

    def test_list_env_templates(self):
        """Test listing public templates when there aren't any

        Create a template; test list public with no
        public templates.
        """
        self._set_policy_rules(
            {'create_env_template': '@',
             'list_env_templates': '@'}
        )

        self.expect_policy_check('create_env_template')
        body = {'name': 'mytemp', 'is_public': False}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertFalse(jsonutils.loads(result.body)['is_public'])

        self.expect_policy_check('create_env_template')
        body = {'name': 'mytemp1', 'is_public': True}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertTrue(jsonutils.loads(result.body)['is_public'])

        self.expect_policy_check('list_env_templates')
        req = self._get('/templates')
        result = req.get_response(self.api)

        self.assertEqual(2, len(jsonutils.loads(result.body)['templates']))

    def test_list_env_templates_with_different_tenant(self):
        """Test listing public template from another tenant

        Create two template in two different tenants;
        test list public template from another tenant.
        """
        self._set_policy_rules(
            {'create_env_template': '@',
             'list_env_templates': '@'}
        )

        self.expect_policy_check('create_env_template')
        body = {'name': 'mytemp', 'is_public': False}
        req = self._post('/templates', jsonutils.dump_as_bytes(body),
                         tenant='first_tenant')
        result = req.get_response(self.api)
        self.assertFalse(jsonutils.loads(result.body)['is_public'])

        self.expect_policy_check('create_env_template')
        body = {'name': 'mytemp1', 'is_public': True}
        req = self._post('/templates', jsonutils.dump_as_bytes(body),
                         tenant='second_tenant')
        result = req.get_response(self.api)
        self.assertTrue(jsonutils.loads(result.body)['is_public'])

        self.expect_policy_check('list_env_templates')
        req = self._get('/templates', tenant='first_tenant')
        result = req.get_response(self.api)

        self.assertEqual(2, len(jsonutils.loads(result.body)['templates']))

    def test_illegal_template_name_create(self):
        """Check that an illegal temp name results in an HTTPClientError."""
        self._set_policy_rules(
            {'list_env_templates': '@',
             'create_env_template': '@',
             'show_env_template': '@'}
        )
        self.expect_policy_check('create_env_template')

        body = {'name': '  '}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(400, result.status_code)

    def test_too_long_template_name_create(self):
        """Check that a long template name results in an HTTPBadResquest."""
        self._set_policy_rules(
            {'list_env_templates': '@',
             'create_env_template': '@',
             'show_env_template': '@'}
        )
        self.expect_policy_check('create_env_template')

        body = {'name': 'a' * 256}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(400, result.status_code)
        result_msg = result.text.replace('\n', '')
        self.assertIn('Environment template name should be 255 characters '
                      'maximum',
                      result_msg)

    def test_mallformed_body(self):
        """Check that an illegal temp name results in an HTTPClientError."""
        self._set_policy_rules(
            {'create_env_template': '@'}
        )
        self.expect_policy_check('create_env_template')

        body = {'invalid': 'test'}
        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(400, result.status_code)

    def test_missing_env_template(self):
        """Check that a missing env template results in an HTTPNotFound."""
        self._set_policy_rules(
            {'show_env_template': '@'}
        )
        self.expect_policy_check('show_env_template',
                                 {'env_template_id': 'no-such-id'})

        req = self._get('/templates/no-such-id')
        result = req.get_response(self.api)
        self.assertEqual(404, result.status_code)

    def test_update_env_template(self):
        """Check that environment rename works."""
        self._set_policy_rules(
            {'show_env_template': '@',
             'update_env_template': '@'}
        )
        self.expect_policy_check('update_env_template',
                                 {'env_template_id': '12345'})

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        expected = dict(
            id='12345',
            is_public=False,
            name='my-temp',
            version=0,
            created=fake_now,
            updated=fake_now,
            tenant_id=self.tenant,
            description_text='',
            description={
                'name': 'my-temp',
                '?': {'id': '12345'}
            }
        )
        e = models.EnvironmentTemplate(**expected)
        test_utils.save_models(e)

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        del expected['description']
        expected['services'] = []
        expected['name'] = 'renamed_temp'
        expected['updated'] = fake_now

        body = {
            'name': 'renamed_temp'
        }
        req = self._put('/templates/12345', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)

        self.expect_policy_check('show_env_template',
                                 {'env_template_id': '12345'})
        req = self._get('/templates/12345')
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)

        expected['created'] = datetime.isoformat(expected['created'])[:-7]
        expected['updated'] = datetime.isoformat(expected['updated'])[:-7]

        self.assertEqual(expected, jsonutils.loads(result.body))

    def test_update_env_template_with_inappropriate_name(self):
        """Check that environment rename works."""
        self._set_policy_rules(
            {'show_env_template': '@',
             'update_env_template': '@'}
        )
        self.expect_policy_check('update_env_template',
                                 {'env_template_id': '12345'})

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        expected = dict(
            id='12345',
            is_public=False,
            name='my-temp',
            version=0,
            created=fake_now,
            updated=fake_now,
            tenant_id=self.tenant
        )
        e = models.EnvironmentTemplate(**expected)
        test_utils.save_models(e)

        # Attempt to update the environment template with invalid name.
        body = {'name': ''}
        req = self._put('/templates/12345', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(400, result.status_code)
        self.assertIn(b'EnvTemplate body is incorrect', result.body)

        # Verify that the name was not changed.
        self.expect_policy_check('show_env_template',
                                 {'env_template_id': '12345'})
        req = self._get('/templates/12345')
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
        self.assertEqual(expected['name'],
                         jsonutils.loads(result.body)['name'])

    def test_delete_env_templates(self):
        """Test that environment deletion results in the correct rpc call."""
        self._set_policy_rules(
            {'delete_env_template': '@'}
        )
        self.expect_policy_check(
            'delete_env_template', {'env_template_id': '12345'}
        )

        fake_now = timeutils.utcnow()
        expected = dict(
            id='12345',
            name='my-temp',
            version=0,
            created=fake_now,
            updated=fake_now,
            tenant_id=self.tenant,
            description={
                'name': 'my-temp',
                '?': {'id': '12345'}
            }
        )
        e = models.EnvironmentTemplate(**expected)
        test_utils.save_models(e)

        req = self._delete('/templates/12345')
        result = req.get_response(self.api)

        # Should this be expected behavior?
        self.assertEqual(b'', result.body)
        self.assertEqual(200, result.status_code)

    def test_create_env_templates_with_applications(self):
        """Create an template, test template.show()."""
        self._set_policy_rules(
            {'list_env_templates': '@',
             'create_env_template': '@',
             'show_env_template': '@'}
        )
        self.expect_policy_check('create_env_template')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now
        expected = {'tenant_id': self.tenant,
                    'id': self.uuids[0],
                    'is_public': False,
                    'name': 'env_template_name',
                    'description_text': '',
                    'version': 0,
                    'created': datetime.isoformat(fake_now)[:-7],
                    'updated': datetime.isoformat(fake_now)[:-7]}

        services = [
            {
                "instance": {
                    "assignFloatingIp": "true",
                    "keyname": "mykeyname",
                    "image": "cloud-fedora-v3",
                    "flavor": "m1.medium",
                    "?": {
                        "type": "io.murano.resources.Linux",
                        "id": "ef984a74-29a4-45c0-b1dc-2ab9f075732e"
                    }
                },
                "name": "orion",
                "port": "8080",
                "?": {
                    "type": "io.murano.apps.apache.Tomcat",
                    "id": "54cea43d-5970-4c73-b9ac-fea656f3c722"
                }
            }
        ]
        expected['services'] = services

        body = {
            "name": "env_template_name",
            "services": [
                {
                    "instance": {
                        "assignFloatingIp": "true",
                        "keyname": "mykeyname",
                        "image": "cloud-fedora-v3",
                        "flavor": "m1.medium",
                        "?": {
                            "type": "io.murano.resources.Linux",
                            "id": "ef984a74-29a4-45c0-b1dc-2ab9f075732e"
                        }
                    },
                    "name": "orion",
                    "port": "8080",
                    "?": {
                        "type": "io.murano.apps.apache.Tomcat",
                        "id": "54cea43d-5970-4c73-b9ac-fea656f3c722"
                    }
                }
            ]
        }

        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(expected, jsonutils.loads(result.body))

        # Reset the policy expectation
        self.expect_policy_check('list_env_templates')

        req = self._get('/templates')
        result = req.get_response(self.api)
        del expected['services']
        self.assertEqual(200, result.status_code)
        self.assertEqual({'templates': [expected]},
                         jsonutils.loads(result.body))

        # Reset the policy expectation
        self.expect_policy_check('show_env_template',
                                 {'env_template_id': self.uuids[0]})
        expected['services'] = services
        req = self._get('/templates/%s' % self.uuids[0])
        result = req.get_response(self.api)
        self.assertEqual(expected, jsonutils.loads(result.body))

    def test_add_application_to_template(self):
        """Create an template, test template.show()."""
        self._set_policy_rules(
            {'create_env_template': '@',
             'add_application': '@'}
        )
        self.expect_policy_check('create_env_template')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now
        services = [
            {
                "instance": {
                    "assignFloatingIp": "true",
                    "keyname": "mykeyname",
                    "image": "cloud-fedora-v3",
                    "flavor": "m1.medium",
                    "?": {
                        "type": "io.murano.resources.Linux",
                        "id": "ef984a74-29a4-45c0-b1dc-2ab9f075732e"
                    }
                },
                "name": "orion",
                "port": "8080",
                "?": {
                    "type": "io.murano.apps.apache.Tomcat",
                    "id": "54cea43d-5970-4c73-b9ac-fea656f3c722"
                }
            }
        ]

        body = {
            "name": "template_name",
        }

        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)

        body = services
        req = self._post('/templates/%s/services' % self.uuids[0],
                         jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)

        self.assertEqual(200, result.status_code)
        self.assertEqual(services, jsonutils.loads(result.body))
        req = self._get('/templates/%s/services' % self.uuids[0])
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
        self.assertEqual(1, len(jsonutils.loads(result.body)))

        service_no_instance = [
            {
                "instance": "ef984a74-29a4-45c0-b1dc-2ab9f075732e",
                "name": "tomcat",
                "port": "8080",
                "?": {
                    "type": "io.murano.apps.apache.Tomcat",
                    "id": "54cea43d-5970-4c73-b9ac-fea656f3c722"
                }
            }
        ]

        req = self._post('/templates/%s/services' % self.uuids[0],
                         jsonutils.dump_as_bytes(service_no_instance))
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)

        req = self._get('/templates/%s/services' % self.uuids[0])
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
        self.assertEqual(2, len(jsonutils.loads(result.body)))

    def test_delete_application_in_template(self):
        """Create an template, test template.show()."""
        self._set_policy_rules(
            {'create_env_template': '@',
             'delete_env_application': '@'}
        )
        self.expect_policy_check('create_env_template')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        body = {
            "name": "mytemplate",
            "services": [
                {
                    "name": "tomcat",
                    "port": "8080",
                    "?": {
                        "type": "io.murano.apps.apache.Tomcat",
                        "id": "54cea43d-5970-4c73-b9ac-fea656f3c722"
                    }
                }
            ]
        }

        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
        self.assertEqual(1, len(jsonutils.loads(result.body)['services']))

        req = self._get('/templates/%s/services' % self.uuids[0])
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
        self.assertEqual(1, len(jsonutils.loads(result.body)))

        service_id = '54cea43d-5970-4c73-b9ac-fea656f3c722'
        req = self._get('/templates/' + self.uuids[0] +
                        '/services/' + service_id)
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)

        req = self._delete('/templates/' + self.uuids[0] +
                           '/services/' + service_id)
        result = req.get_response(self.api)

        self.assertEqual(200, result.status_code)
        self.assertEqual(0, len(jsonutils.loads(result.body)['services']))

        req = self._get('/templates/' + self.uuids[0] +
                        '/services/' + service_id)
        result = req.get_response(self.api)
        self.assertEqual(404, result.status_code)

    def test_create_environment(self):
        """Test that environment is created, session configured."""

        self.fixture = self.useFixture(config_fixture.Config())
        self.fixture.conf(args=[])

        self._set_policy_rules(
            {'create_env_template': '@',
             'create_environment': '@'}
        )

        self._create_env_template_no_service()
        body_env = {'name': 'my_template'}

        self.expect_policy_check('create_environment',
                                 {'env_template_id': self.uuids[0]})
        req = self._post('/templates/%s/create-environment' %
                         self.uuids[0], jsonutils.dump_as_bytes(body_env))
        session_result = req.get_response(self.api)
        self.assertEqual(200, session_result.status_code)
        self.assertIsNotNone(session_result)
        body_returned = jsonutils.loads(session_result.body)
        self.assertEqual(self.uuids[4], body_returned['session_id'])
        self.assertEqual(self.uuids[3], body_returned['environment_id'])

    @mock.patch('murano.db.services.environments.EnvironmentServices.create')
    def test_create_environment_handle_duplicate_exc(self, mock_function):
        """Test that duplicate entry exception is correctly handled."""
        mock_function.side_effect = db_exc.DBDuplicateEntry

        self.fixture = self.useFixture(config_fixture.Config())
        self.fixture.conf(args=[])

        self._set_policy_rules(
            {'create_env_template': '@',
             'create_environment': '@'}
        )

        self._create_env_template_no_service()
        body_env = {'name': 'my_template'}

        self.expect_policy_check('create_environment',
                                 {'env_template_id': self.uuids[0]})
        req = self._post('/templates/%s/create-environment' %
                         self.uuids[0], jsonutils.dump_as_bytes(body_env))
        session_result = req.get_response(self.api)
        self.assertEqual(409, session_result.status_code)

    def test_create_env_with_template_and_services(self):
        """Test env and session creation with services

        Test that environment is created and session with template
        with services.
        """
        self.fixture = self.useFixture(config_fixture.Config())
        self.fixture.conf(args=[])
        self._set_policy_rules(
            {'create_env_template': '@',
             'create_environment': '@'}
        )
        self._create_env_template_services()

        self.expect_policy_check('create_environment',
                                 {'env_template_id': self.uuids[0]})
        body = {'name': 'my_template'}
        req = self._post('/templates/%s/create-environment' %
                         self.uuids[0], jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)

        self.assertIsNotNone(result)
        self.assertEqual(200, result.status_code)
        body_returned = jsonutils.loads(result.body)
        self.assertEqual(self.uuids[4], body_returned['session_id'])
        self.assertEqual(self.uuids[3], body_returned['environment_id'])

    def test_create_env_with_template_no_services(self):
        """Test env and session creation without services

        Test that environment is created and session with template
        without services.
        """
        self.fixture = self.useFixture(config_fixture.Config())
        self.fixture.conf(args=[])
        self._set_policy_rules(
            {'create_env_template': '@',
             'create_environment': '@'}
        )
        self._create_env_template_no_service()

        self.expect_policy_check('create_environment',
                                 {'env_template_id': self.uuids[0]})
        body = {'name': 'my_template'}

        req = self._post('/templates/%s/create-environment' %
                         self.uuids[0], jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertIsNotNone(result)
        self.assertEqual(200, result.status_code)
        body_returned = jsonutils.loads(result.body)
        self.assertEqual(self.uuids[4], body_returned['session_id'])
        self.assertEqual(self.uuids[3], body_returned['environment_id'])

    def test_update_service_in_template(self):
        """Test the service is updated in the environment template"""
        self.fixture = self.useFixture(config_fixture.Config())
        self.fixture.conf(args=[])
        self._set_policy_rules(
            {'create_env_template': '@',
             'update_service_env_template': '@'}
        )
        updated_env = "UPDATED_ENV"
        env_template = self._create_env_template_services()
        self.expect_policy_check('update_service_env_template')
        env_template["name"] = updated_env

        req = self._put('/templates/{0}/services/{1}'.
                        format(self.uuids[0], "service_id"),
                        jsonutils.dump_as_bytes(env_template))
        result = req.get_response(self.api)
        self.assertIsNotNone(result)
        self.assertEqual(200, result.status_code)
        body_returned = jsonutils.loads(result.body)
        self.assertEqual(updated_env, body_returned['name'])

    def test_mallformed_env_body(self):
        """Check that an illegal temp name results in an HTTPClientError."""
        self._set_policy_rules(
            {'create_env_template': '@',
             'create_environment': '@'}
        )
        self._create_env_template_no_service()

        self.expect_policy_check('create_environment',
                                 {'env_template_id': self.uuids[0]})
        body = {'invalid': 'test'}
        req = self._post('/templates/%s/create-environment' %
                         self.uuids[0], jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(400, result.status_code)

    def test_delete_notexisting_service(self):
        """Check deleting a not existing service, return a 404 error."""
        self._set_policy_rules(
            {'create_env_template': '@',
             'delete_env_application': '@'}
        )
        self.expect_policy_check('create_env_template')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        body = {
            "name": "mytemplate",
            "services": [
                {
                    "name": "tomcat",
                    "port": "8080",
                    "?": {
                        "type": "io.murano.apps.apache.Tomcat",
                        "id": "ID1"
                    }
                }
            ]
        }

        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
        self.assertEqual(1, len(jsonutils.loads(result.body)['services']))

        req = self._delete('/templates/{0}/services/{1}'.format(self.uuids[0],
                                                                "NO_EXIST"))
        result = req.get_response(self.api)
        self.assertEqual(404, result.status_code)

    @mock.patch('murano.db.services.environment_templates.EnvTemplateServices.'
                'get_env_template')
    def test_validate_request_handle_forbidden_exc(self, mock_function):
        """Test whether forbidden exception is thrown with different tenant."""
        self._set_policy_rules(
            {'create_env_template': '@',
             'show_env_template': '@',
             'show_env_template': '@'}
        )

        # If is_public is False, then exception should be thrown.
        mock_env_template = mock.MagicMock(is_public=False, tenant_id=-1)
        mock_function.return_value = mock_env_template

        self._create_env_template_no_service()
        self.expect_policy_check('show_env_template',
                                 {'env_template_id': self.uuids[0]})
        req = self._get('/templates/%s' % self.uuids[0])
        result = req.get_response(self.api)
        self.assertEqual(result.status_code, 403)

        # If is_public is True, then no exception should be thrown.
        mock_env_template = mock.MagicMock(is_public=True, tenant_id=-1)
        mock_function.return_value = mock_env_template

        self.expect_policy_check('show_env_template',
                                 {'env_template_id': self.uuids[0]})
        req = self._get('/templates/%s' % self.uuids[0])
        result = req.get_response(self.api)
        self.assertEqual(result.status_code, 200)

    def test_create_env_notexisting_templatebody(self):
        """Check that an illegal temp name results in an HTTPClientError."""
        self._set_policy_rules(
            {'create_environment': '@'}
        )
        env_template_id = 'noexisting'
        self.expect_policy_check('create_environment',
                                 {'env_template_id': env_template_id})

        body = {'name': 'test'}
        req = self._post('/templates/%s/create-environment'
                         % env_template_id, jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        self.assertEqual(404, result.status_code)

    def _create_env_template_no_service(self):
        self.expect_policy_check('create_env_template')
        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        req = self._post('/templates',
                         jsonutils.dump_as_bytes({'name': 'name'}))
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)

    def _create_env_template_services(self):
        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        self.expect_policy_check('create_env_template')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now
        body = {
            "name": "env_template_name",
            "services": [
                {
                    "instance": {
                        "assignFloatingIp": "true",
                        "keyname": "mykeyname",
                        "image": "cloud-fedora-v3",
                        "flavor": "m1.medium",
                        "?": {
                            "type": "io.murano.resources.Linux",
                            "id": "ef984a74-29a4-45c0-b1dc-2ab9f075732e"
                        }
                    },
                    "name": "orion",
                    "port": "8080",
                    "?": {
                        "type": "io.murano.apps.apache.Tomcat",
                        "id": "service_id"
                    }
                }
            ]
        }

        req = self._post('/templates', jsonutils.dump_as_bytes(body))
        result = req.get_response(self.api)
        return result.json
