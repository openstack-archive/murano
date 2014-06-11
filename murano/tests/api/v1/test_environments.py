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
from webob import exc

from murano.api.v1 import environments
from murano.db import models
from murano.openstack.common import timeutils
import murano.tests.api.base as test_base
import murano.tests.utils as test_utils


class TestEnvironmentApi(test_base.ControllerTest, test_base.MuranoTestCase):
    RPC_IMPORT = 'murano.db.services.environments.rpc'

    def setUp(self):
        super(TestEnvironmentApi, self).setUp()
        self.controller = environments.Controller()

    def test_list_empty_environments(self):
        """Check that with no environments an empty list is returned"""
        req = self._get('/environments')
        result = self.controller.index(req)
        self.assertEqual({'environments': []}, result)

    def test_create_environment(self):
        """Create an environment, test environment.show()"""
        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        uuids = ('env_object_id', 'network_id', 'environment_id')
        mock_uuid = self._stub_uuid(uuids)

        expected = {'tenant_id': self.tenant,
                    'id': 'environment_id',
                    'name': 'my_env',
                    'networking': {},
                    'version': 0,
                    'created': fake_now,
                    'updated': fake_now}

        body = {'name': 'my_env'}
        req = self._post('/environments', json.dumps(body))
        result = self.controller.create(req, body)
        self.assertEqual(expected, result)

        expected['status'] = 'ready'

        req = self._get('/environments')
        result = self.controller.index(req)

        self.assertEqual({'environments': [expected]}, result)

        expected['services'] = []

        req = self._get('/environments/%s' % uuids[-1])
        result = self.controller.show(req, uuids[-1])

        self.assertEqual(expected, result)
        self.assertEqual(3, mock_uuid.call_count)

    def test_missing_environment(self):
        """Check that a missing environment results in an HTTPNotFound"""
        req = self._get('/environments/no-such-id')
        self.assertRaises(exc.HTTPNotFound, self.controller.show,
                          req, 'no-such-id')

    def test_update_environment(self):
        """Check that environment rename works"""
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
                'Attributes': {}
            }
        )
        e = models.Environment(**expected)
        test_utils.save_models(e)

        fake_now = timeutils.utcnow()
        timeutils.utcnow.override_time = fake_now

        del expected['description']
        expected['services'] = []
        expected['status'] = 'ready'
        expected['name'] = 'renamed env'
        expected['updated'] = fake_now

        body = {
            'name': 'renamed env'
        }
        req = self._post('/environments/12345', json.dumps(body))
        result = self.controller.update(req, '12345', body)

        req = self._get('/environments/%s' % '12345')
        result = self.controller.show(req, '12345')

        self.assertEqual(expected, result)

    def test_delete_environment(self):
        """Test that environment deletion results in the correct rpc call"""
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

        rpc_task = {
            'tenant_id': self.tenant,
            'model': {'Attributes': {}, 'Objects': None},
            'token': None
        }

        req = self._delete('/environments/12345')
        result = self.controller.delete(req, '12345')

        self.mock_engine_rpc.handle_task.assert_called_once_with(rpc_task)

        # Should this be expected behavior?
        self.assertEqual(None, result)
