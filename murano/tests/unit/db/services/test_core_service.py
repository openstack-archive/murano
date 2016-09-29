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

import mock
from webob import exc

from murano.db.services import core_services
from murano.tests.unit import base
from murano.tests.unit.db.services import environment_templates as et


class TestCoreServices(base.MuranoTestCase):
    def setUp(self):
        super(TestCoreServices, self).setUp()
        self.core_services = core_services.CoreServices
        self.addCleanup(mock.patch.stopall)

    @mock.patch('murano.db.services.environment_templates.EnvTemplateServices')
    def test_empty_template(self, template_services_mock):
        """Check obtaining the template description without services."""
        fixture = self.useFixture(et.EmptyEnvironmentTemplateFixture())
        template_services_mock.get_description.return_value = \
            fixture.environment_template_desc
        template_des = self.core_services.get_template_data('any', '/services')
        self.assertEqual([], template_des)
        template_services_mock.get_description.assert_called_with('any')

    @mock.patch('murano.db.services.environment_templates.EnvTemplateServices')
    def test_template_services(self, template_services_mock):
        """Check obtaining the template description with services."""
        fixture_apps = self.useFixture(et.ApplicationsFixture())
        fixture_env_apps = self.useFixture(et.AppEnvTemplateFixture())
        template_services_mock.get_description.return_value = \
            fixture_env_apps.env_template_desc
        template_des = self.core_services.get_template_data('any', '/services')
        self.assertEqual(fixture_apps.applications_desc, template_des)
        template_services_mock.get_description.assert_called_with('any')

    @mock.patch('murano.db.services.environment_templates.EnvTemplateServices')
    def test_template_get_service(self, template_services_mock):
        """Check obtaining the service description."""
        fixture = self.useFixture(et.AppEnvTemplateFixture())
        fixture2 = self.useFixture(et.ApplicationTomcatFixture())
        template_services_mock.get_description.return_value = \
            fixture.env_template_desc
        template_des = \
            self.core_services.get_template_data('any',
                                                 '/services/tomcat_id')
        self.assertEqual(fixture2.application_tomcat_desc, template_des)
        template_services_mock.get_description.assert_called_with('any')

    @mock.patch('murano.db.services.environment_templates.EnvTemplateServices')
    def test_template_post_services(self, template_services_mock):
        """Check adding a service to a template."""
        fixture = self.useFixture(et.EmptyEnvironmentTemplateFixture())
        fixture2 = self.useFixture(et.AppEnvTemplateFixture())
        template_services_mock.get_description.return_value = \
            fixture.environment_template_desc
        template_des = self.core_services.\
            post_env_template_data('any',
                                   fixture2.env_template_desc,
                                   '/services')
        self.assertEqual(fixture2.env_template_desc, template_des)
        template_services_mock.get_description.assert_called_with('any')

    @mock.patch('murano.db.services.environment_templates.EnvTemplateServices')
    def test_template_delete_services(self, template_services_mock):
        """Check deleting a service in a template."""
        fixture2 = self.useFixture(et.AppEnvTemplateFixture())
        fixture = self.useFixture(et.ApplicationTomcatFixture())
        template_services_mock.get_description.return_value = \
            fixture2.env_template_desc
        self.core_services.\
            delete_env_template_data('any',
                                     '/services/54aaa43d-5970')
        template_des = self.core_services.get_template_data('any', '/services')
        self.assertEqual([fixture.application_tomcat_desc], template_des)
        template_services_mock.get_description.assert_called_with('any')

    @mock.patch('murano.db.services.environment_templates.EnvTemplateServices')
    def test_get_template_no_exists(self, template_services_mock):
        """Check obtaining a non-existing service."""
        fixture2 = self.useFixture(et.AppEnvTemplateFixture())

        template_services_mock.get_description.return_value = \
            fixture2.env_template_desc
        self.assertRaises(exc.HTTPNotFound,
                          self.core_services.get_template_data,
                          'any', '/services/noexists')
        template_services_mock.get_description.assert_called_with('any')

    @mock.patch('murano.db.services.environment_templates.EnvTemplateServices')
    def test_adding_services(self, template_services_mock):
        """Check adding services to a template."""
        ftomcat = self.useFixture(et.ApplicationTomcatFixture())
        fmysql = self.useFixture(et.ApplicationMysqlFixture())
        fixture = self.useFixture(et.EmptyEnvironmentTemplateFixture())
        fservices = self.useFixture(et.ApplicationsFixture())
        template_services_mock.get_description.return_value =\
            fixture.environment_template_desc
        self.core_services.\
            post_env_template_data('any',
                                   ftomcat.application_tomcat_desc,
                                   '/services')
        self.core_services.\
            post_env_template_data('any',
                                   fmysql.application_mysql_desc,
                                   '/services')
        template_des = \
            self.core_services.get_template_data('any', '/services')
        self.assertEqual(fservices.applications_desc, template_des)
        template_services_mock.get_description.assert_called_with('any')

    @mock.patch('murano.db.services.environment_templates.EnvTemplateServices')
    def test_none_temp_description(self, template_services_mock):
        fixture = self.useFixture(et.EmptyEnvironmentTemplateFixture())
        template_services_mock.get_description.return_value = None
        self.assertIsNone(self.core_services.
                          get_template_data('any', '/services'))
        self.assertRaises(exc.HTTPNotFound,
                          self.core_services.post_env_template_data,
                          'any', fixture.environment_template_desc,
                          '/services')
        self.assertRaises(exc.HTTPNotFound,
                          self.core_services.post_application_data,
                          'any', fixture.environment_template_desc,
                          '/services')
        self.assertRaises(exc.HTTPNotFound,
                          self.core_services.delete_env_template_data,
                          'any', '/services')
        self.assertRaises(exc.HTTPNotFound,
                          self.core_services.put_application_data,
                          'any', fixture.environment_template_desc,
                          '/services')

    @mock.patch('murano.common.utils.TraverseHelper')
    @mock.patch('murano.db.services.environments.EnvironmentServices')
    def test_post_data(self, env_services_mock, source_mock):
        fixture = self.useFixture(et.EmptyEnvironmentFixture())
        env_services_mock.get_description.return_value = fixture.env_desc
        session_id = None
        ftomcat = self.useFixture(et.ApplicationTomcatFixture())
        self.assertEqual(self.core_services.post_data('any', session_id,
                         ftomcat.application_tomcat_desc,
                         '/services'), ftomcat.application_tomcat_desc)
        self.assertTrue(source_mock.insert.called)

        self.assertEqual(self.core_services.put_data('any', session_id,
                         ftomcat.application_tomcat_desc,
                         '/services'), ftomcat.application_tomcat_desc)
        self.assertTrue(source_mock.update.called)

        self.core_services.delete_data('any', session_id, '/services')
        self.assertTrue(source_mock.remove.called)

    @mock.patch('murano.db.services.environments.EnvironmentServices')
    def test_get_service_status(self, env_services_mock):
        service_id = 12
        fixture = self.useFixture(et.EmptyEnvironmentFixture())
        env_services_mock.get_description.return_value = fixture.env_desc
        self.core_services.get_service_status('any', service_id)
        self.assertTrue(env_services_mock.get_status.called)
