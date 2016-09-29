# Copyright (c) 2015 Telefonica I+D.

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

import fixtures
import mock

from murano.db.services import environment_templates as env_temp
from murano.tests.unit import base
from murano.tests.unit.db.services import environment_templates as et


class TestTemplateServices(base.MuranoWithDBTestCase,
                           fixtures.TestWithFixtures):

    def setUp(self):
        super(TestTemplateServices, self).setUp()
        self.template_services = env_temp.EnvTemplateServices
        self.uuids = ['template_id', 'template_id2']
        self.mock_uuid = self._stub_uuid(self.uuids)
        self.addCleanup(mock.patch.stopall)

    def test_create_template(self):
        """Check creating a template without services."""
        fixture = self.useFixture(et.EmptyEnvironmentTemplateFixture())
        """Check the creation of a template."""
        body = {
            "name": "my_template"
        }
        template_des = self.template_services.create(body, 'tenant_id')
        self.assertEqual(fixture.environment_template_desc,
                         template_des.description)

    def test_clone_template(self):
        """Check the clonation of a template."""
        body = {
            "name": "my_template"
        }
        template = self.template_services.create(body, 'tenant_id')
        cloned_template = self.template_services.clone(template['id'],
                                                       'id2',
                                                       "my_template2", False)
        self.assertEqual(cloned_template.description['name'], 'my_template2')
        self.assertEqual(cloned_template.description['tenant_id'], 'id2')

    def test_get_empty_template(self):
        """Check obtaining information about a template without services."""
        fixture = self.useFixture(et.EmptyEnvironmentTemplateFixture())
        self.test_create_template()
        template = \
            self.template_services.get_description("template_id")
        self.assertEqual(fixture.environment_template_desc, template)

    def test_get_template_services(self):
        """Check obtaining information about a template with services."""
        fixture = self.useFixture(et.AppEnvTemplateFixture())
        template = self.template_services.create(fixture.env_template_desc,
                                                 'tenant_id')
        self.assertEqual(fixture.env_template_desc, template.description)
        template_des = \
            self.template_services.get_description("template_id")
        self.assertEqual(fixture.env_template_desc, template_des)

    def test_get_template_no_exists(self):
        """Check obtaining information about a non-existent template

        Check obtaining information about a template which
        does not exist.
        """
        self.assertRaises(ValueError,
                          self.template_services.get_description,
                          'no_exists')

    def test_delete_template(self):
        """Check deleting a template."""
        self.test_create_template()
        self.template_services.delete("template_id")

    def _stub_uuid(self, values=None):
        class FakeUUID(object):
            def __init__(self, v):
                self.hex = v

        if values is None:
            values = []
        mock_uuid4 = mock.patch('uuid.uuid4').start()
        mock_uuid4.side_effect = [FakeUUID(v) for v in values]
        return mock_uuid4

    def test_get_application_description(self):
        fixture = self.useFixture(et.AppEnvTemplateFixture())
        self.template_services.create(fixture.env_template_desc,
                                      'tenant_id')
        template_app_des = (self.template_services.
                            get_application_description("template_id"))
        self.assertEqual(template_app_des,
                         fixture.env_template_desc['services'])

        body = {
            "name": "my_template"
        }
        self.template_services.create(body, 'tenant_id')
        template_app_des_2 = (self.template_services.
                              get_application_description("template_id2"))
        self.assertEqual([], template_app_des_2)
