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

import fixtures
from oslo_log import log as logging
import testtools

from murano.common import config
from murano.db import api as db_api

CONF = config.CONF
logging.register_options(CONF)
logging.setup(CONF, 'murano')


class MuranoTestCase(testtools.TestCase):

    def setUp(self):
        super(MuranoTestCase, self).setUp()
        self.useFixture(fixtures.FakeLogger('murano'))

    def override_config(self, name, override, group=None):
        CONF.set_override(name, override, group)
        self.addCleanup(CONF.clear_override, name, group)


class MuranoWithDBTestCase(MuranoTestCase):

    def setUp(self):
        super(MuranoWithDBTestCase, self).setUp()
        self.override_config('connection', "sqlite://", group='database')
        db_api.setup_db()
        self.addCleanup(db_api.drop_db)

        self.override_config('env_audit_enabled', False, group='stats')


class MuranoNotifyWithDBTestCase(MuranoWithDBTestCase):

    def setUp(self):
        super(MuranoNotifyWithDBTestCase, self).setUp()
        self.override_config('connection', "sqlite://", group='database')
        db_api.setup_db()
        self.addCleanup(db_api.drop_db)
        self.override_config('env_audit_enabled', True, group='stats')
