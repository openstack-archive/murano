# coding: utf-8
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json

from oslo.config import cfg
from oslo.utils import timeutils

from murano.api.v1 import environments
from murano.common import config
from murano.db import models
import murano.tests.unit.api.base as tb
import murano.tests.unit.utils as test_utils


class TestEnvironmentApi(tb.ControllerTest, tb.MuranoApiTestCase):
    def setUp(self):
        super(TestEnvironmentApi, self).setUp()
        self.controller = environments.Controller()

    def test_list_empty_environments(self):
        """Check that with no environments an empty list is returned."""
        self._set_policy_rules(
            {'list_environments': '@'}
        )
        self.expect_policy_check('list_environments')

        req = self._get('/environments')
        result = req.get_response(self.api)
        self.assertEqual({'environments': []}, json.loads(result.body))

    def test_create_environment(self):
        """Create an environment, test environment.show()."""
        opts = [
            cfg.StrOpt('config_dir'),
            cfg.StrOpt('config_file', default='murano.conf'),
            cfg.StrOpt('project', default='murano'),
        ]
        config.CONF.register_opts(opts)
        self._set_policy_rules(
            {'list_environments': '@',
             'create_environment': '@',
             'show_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        uuids = ('env_object_id', 'network_id', 'environment_id')
        mock_uuid = self._stub_uuid(uuids)

        expected = {'tenant_id': self.tenant,
                    'id': 'environment_id',
                    'name': 'my_env',
                    'networking': {},
                    'version': 0,
                    # TODO(sjmc7) - bug 1347298
                    'created': timeutils.isotime(fake_now)[:-1],
                    'updated': timeutils.isotime(fake_now)[:-1]}

        body = {'name': 'my_env'}
        req = self._post('/environments', json.dumps(body))
        result = req.get_response(self.api)
        self.assertEqual(expected, json.loads(result.body))

        expected['status'] = 'ready'

        # Reset the policy expectation
        self.expect_policy_check('list_environments')

        req = self._get('/environments')
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)
        self.assertEqual({'environments': [expected]}, json.loads(result.body))

        expected['services'] = []

        # Reset the policy expectation
        self.expect_policy_check('show_environment',
                                 {'environment_id': uuids[-1]})

        req = self._get('/environments/%s' % uuids[-1])
        result = req.get_response(self.api)

        self.assertEqual(expected, json.loads(result.body))
        self.assertEqual(3, mock_uuid.call_count)

    def test_illegal_environment_name_create(self):
        """Check that an illegal env name results in an HTTPClientError."""
        self._set_policy_rules(
            {'list_environments': '@',
             'create_environment': '@',
             'show_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        body = {'name': 'my+#env'}
        req = self._post('/environments', json.dumps(body))
        result = req.get_response(self.api)
        self.assertEqual(400, result.status_code)

    def test_unicode_environment_name_create(self):
        """Check that an unicode env name results in an HTTPClientError."""
        self._set_policy_rules(
            {'list_environments': '@',
             'create_environment': '@',
             'show_environment': '@'}
        )
        self.expect_policy_check('create_environment')

        body = {'name': u'yaql ♥ unicode'.encode('utf-8')}
        req = self._post('/environments', json.dumps(body))
        result = req.get_response(self.api)
        self.assertEqual(400, result.status_code)

    def test_missing_environment(self):
        """Check that a missing environment results in an HTTPNotFound."""
        self._set_policy_rules(
            {'show_environment': '@'}
        )
        self.expect_policy_check('show_environment',
                                 {'environment_id': 'no-such-id'})

        req = self._get('/environments/no-such-id')
        result = req.get_response(self.api)
        self.assertEqual(404, result.status_code)

    def test_update_environment(self):
        """Check that environment rename works."""
        self._set_policy_rules(
            {'show_environment': '@',
             'update_environment': '@'}
        )
        self.expect_policy_check('update_environment',
                                 {'environment_id': '12345'})

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        expected = dict(
            id='12345',
            name='my-env',
            version=0,
            networking={},
            created=fake_now,
            updated=fake_now,
            tenant_id=self.tenant,
            description={
                'Objects': {
                    '?': {'id': '12345'}
                },
                'Attributes': []
            }
        )
        e = models.Environment(**expected)
        test_utils.save_models(e)

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        del expected['description']
        expected['services'] = []
        expected['status'] = 'ready'
        expected['name'] = 'renamed_env'
        expected['updated'] = fake_now

        body = {
            'name': 'renamed_env'
        }
        req = self._put('/environments/12345', json.dumps(body))
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)

        self.expect_policy_check('show_environment',
                                 {'environment_id': '12345'})
        req = self._get('/environments/12345')
        result = req.get_response(self.api)
        self.assertEqual(200, result.status_code)

        expected['created'] = timeutils.isotime(expected['created'])[:-1]
        expected['updated'] = timeutils.isotime(expected['updated'])[:-1]

        self.assertEqual(expected, json.loads(result.body))

    def test_delete_environment(self):
        """Test that environment deletion results in the correct rpc call."""
        self._set_policy_rules(
            {'delete_environment': '@'}
        )
        self.expect_policy_check(
            'delete_environment', {'environment_id': '12345'}
        )

        fake_now = timeutils.utcnow()
        expected = dict(
            id='12345',
            name='my-env',
            version=0,
            networking={},
            created=fake_now,
            updated=fake_now,
            tenant_id=self.tenant,
            description={
                'Objects': {
                    '?': {'id': '12345'}
                },
                'Attributes': {}
            }
        )
        e = models.Environment(**expected)
        test_utils.save_models(e)

        req = self._delete('/environments/12345')
        result = req.get_response(self.api)

        # Should this be expected behavior?
        self.assertEqual('', result.body)
        self.assertEqual(200, result.status_code)
