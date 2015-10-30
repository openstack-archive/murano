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

from murano.db import models
from murano.db import session
from murano.tests.unit import base


class TestModels(base.MuranoWithDBTestCase):
    def test_missing_blob(self):
        """Fake a package with NULL supplier JSON blob to test bug 1342306."""
        con = session.get_session().connection()
        con.execute("INSERT INTO package(id, fully_qualified_name, "
                    "owner_id, name, description, created, updated, type, "
                    "supplier) "
                    "VALUES (1, 'blob.test', 1, 'blob test', 'Desc', "
                    "'2014-07-15 00:00:00', '2014-07-15 00:00:00', "
                    "'Application', NULL)")
        loaded_e = session.get_session().query(models.Package).get(1)
        self.assertIsNone(loaded_e.supplier)
