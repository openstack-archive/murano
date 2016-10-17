# Copyright 2016 AT&T Corp
# All Rights Reserved.
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

from murano.db import models
from murano.db.services import cf_connections
from murano.db.services import environments
from murano.db import session as db_session
from murano.tests.unit import base


class TestCFConnection(base.MuranoWithDBTestCase):

    def setUp(self):
        super(TestCFConnection, self).setUp()
        self.resources = []
        self.tenant_id = 'test_tenant_id'

        environment = models.Environment(
            name='test_environment',
            tenant_id='test_tenant_id',
            version=1
        )
        alt_environment = models.Environment(
            name='alt_test_environment',
            tenant_id='alt_test_tenant_id',
            version=1
        )

        unit = db_session.get_session()
        with unit.begin():
            unit.add_all([environment, alt_environment])

        self.environment_id = environment.id
        self.alt_environment_id = alt_environment.id

    def tearDown(self):
        super(TestCFConnection, self).tearDown()
        unit = db_session.get_session()

        if self.environment_id:
            environments.EnvironmentServices.remove(self.environment_id)
        if self.alt_environment_id:
            environments.EnvironmentServices.remove(self.alt_environment_id)

        for resource in self.resources:
            if resource:
                with unit.begin():
                    unit.delete(resource)

    def _create_resource(self, resource_name, **kwargs):
        unit = db_session.get_session()
        model = None
        new_resource_id = 1

        if resource_name == 'cf_org':
            model = models.CFOrganization
        elif resource_name == 'cf_space':
            model = models.CFSpace
        elif resource_name == 'cf_service':
            model = models.CFServiceInstance

        resource = unit.query(model).order_by(model.id.desc()).first()
        if resource:
            new_resource_id = int(resource.id) + 1
        new_resource = model(id=new_resource_id, **kwargs)

        with unit.begin():
            unit.add(new_resource)

        created_resource = unit.query(model)\
            .order_by(model.id.desc()).first()
        self.assertIsNotNone(created_resource)
        self.assertEqual(created_resource.id, str(new_resource.id))
        self.resources.append(created_resource)

        return created_resource

    def test_set_tenant_for_org(self):
        cf_org = self._create_resource('cf_org', tenant=self.tenant_id)
        cf_connections.set_tenant_for_org(cf_org.id, 'another_test_tenant_id')

        duplicate_cf_org = None
        unit = db_session.get_session()
        with unit.begin():
            duplicate_cf_org = unit.query(models.CFOrganization).get(cf_org.id)
        self.assertIsNotNone(duplicate_cf_org)
        self.assertEqual('another_test_tenant_id',
                         duplicate_cf_org.tenant)

    def test_set_environment_for_space(self):
        cf_space = self._create_resource('cf_space',
                                         environment_id=self.environment_id)
        cf_connections.set_environment_for_space(cf_space.id,
                                                 self.alt_environment_id)

        duplicate_cf_space = None
        unit = db_session.get_session()
        with unit.begin():
            duplicate_cf_space = unit.query(models.CFSpace).get(cf_space.id)
        self.assertIsNotNone(duplicate_cf_space)
        self.assertEqual(self.alt_environment_id,
                         duplicate_cf_space.environment_id)

    def test_set_instance_for_service(self):
        cf_service = self._create_resource('cf_service',
                                           service_id='123',
                                           environment_id=self.environment_id,
                                           tenant=self.tenant_id)
        cf_connections.set_instance_for_service(
            instance_id=cf_service.id, service_id='123',
            environment_id=self.alt_environment_id, tenant=self.tenant_id)

        duplicate_cf_service = None
        unit = db_session.get_session()
        with unit.begin():
            duplicate_cf_service = unit.query(models.CFServiceInstance).\
                get(cf_service.id)
        self.assertIsNotNone(duplicate_cf_service)
        self.assertEqual(self.alt_environment_id,
                         duplicate_cf_service.environment_id)

    def test_get_environment_for_space(self):
        cf_space = self._create_resource('cf_space',
                                         environment_id=self.environment_id)
        retrieved_env_id =\
            cf_connections.get_environment_for_space(cf_space.id)
        self.assertEqual(cf_space.environment_id,
                         retrieved_env_id)

    def test_get_tenant_for_org(self):
        cf_org = self._create_resource('cf_org', tenant=self.tenant_id)
        retrieved_tenant =\
            cf_connections.get_tenant_for_org(cf_org.id)
        self.assertEqual(self.tenant_id, retrieved_tenant)

    def test_get_service_for_instance(self):
        cf_service = self._create_resource('cf_service',
                                           service_id='123',
                                           environment_id=self.environment_id,
                                           tenant=self.tenant_id)
        retrieved_service =\
            cf_connections.get_service_for_instance(cf_service.id)
        for attr in ['id', 'environment_id', 'service_id', 'tenant']:
            self.assertEqual(getattr(cf_service, attr),
                             getattr(retrieved_service, attr))

    def test_delete_environment_from_space(self):
        environment = models.Environment(
            name='test_environment_1',
            tenant_id='test_tenant_id_1',
            version=1
        )
        unit = db_session.get_session()
        with unit.begin():
            unit.add(environment)

        cf_connections.delete_environment_from_space(environment.id)
        with unit.begin():
            retrieved_env = unit.query(models.Environment).get(environment.id)
            self.assertIsNotNone(retrieved_env)
