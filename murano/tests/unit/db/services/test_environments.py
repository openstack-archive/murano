#    Copyright (c) 2015 Mirantis, Inc.
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
import datetime as dt

from oslo.utils import timeutils

from murano.db import models
from murano.db.services import environments
from murano.db import session as db_session
from murano.services import states
from murano.tests.unit import base


class TestEnvironmentServices(base.MuranoWithDBTestCase):
    def test_environment_ready_if_last_session_deployed_after_failed(self):
        """If last session was deployed successfully and other session
        was failed - environment must have status "ready".

        Bug: #1413260
        """
        OLD_VERSION = 0
        LATEST_VERSION = 1

        session = db_session.get_session()

        environment = models.Environment(
            name='test_environment', tenant_id='test_tenant_id',
            version=LATEST_VERSION
        )
        session.add(environment)

        now = timeutils.utcnow()

        session_1 = models.Session(
            environment=environment, user_id='test_user_id_1',
            version=OLD_VERSION,
            state=states.SessionState.DEPLOY_FAILURE,
            updated=now, description={}
        )
        session_2 = models.Session(
            environment=environment, user_id='test_user_id_2',
            version=LATEST_VERSION,
            state=states.SessionState.DEPLOYED,
            updated=now + dt.timedelta(minutes=1), description={}
        )
        session.add_all([session_1, session_2])
        session.flush()

        expected_status = states.EnvironmentStatus.READY
        actual_status = environments.EnvironmentServices.get_status(
            environment.id
        )

        self.assertEqual(actual_status, expected_status)
