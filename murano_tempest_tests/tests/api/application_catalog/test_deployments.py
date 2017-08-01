#    Copyright (c) 2017 AT&T Corporation.
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

from tempest.lib import decorators

from murano_tempest_tests.tests.api.application_catalog import base
from murano_tempest_tests import utils


class TestDeployments(base.BaseApplicationCatalogTest):

    def _create_and_deploy_env_session(self):
        name = utils.generate_name('_create_and_deploy_env_session')
        environment = self.application_catalog_client.create_environment(
            name)
        self.addCleanup(self.application_catalog_client.delete_environment,
                        environment['id'])
        session = self.application_catalog_client.create_session(
            environment['id'])
        self.addCleanup(self.application_catalog_client.delete_session,
                        environment['id'], session['id'])
        self.application_catalog_client.deploy_session(environment['id'],
                                                       session['id'])
        utils.wait_for_environment_deploy(self.application_catalog_client,
                                          environment['id'])
        return environment

    @decorators.idempotent_id('ea4f6f21-bd97-4b58-af93-6fe5417543f9')
    def test_list_all_deployments(self):
        # Given two environments with deployments
        environment1 = self._create_and_deploy_env_session()
        environment2 = self._create_and_deploy_env_session()

        # When list_all_deployments is called
        deployments = self.application_catalog_client.list_all_deployments()

        # Then both environment's deployments are returned
        self.assertEqual(2, len(deployments))
        environment_ids = [d['environment_id'] for d in deployments]
        self.assertIn(environment1['id'], environment_ids)
        self.assertIn(environment2['id'], environment_ids)

    @decorators.idempotent_id('d76706f6-9281-4fdc-9758-57da825311b1')
    def test_list_deployments(self):
        # Given two environments with deployments
        environment1 = self._create_and_deploy_env_session()
        self._create_and_deploy_env_session()

        # When list_deployments is called for first environment
        deployments = self.application_catalog_client.list_deployments(
            environment1['id'])

        # Then only the first environment's deployment is returned
        self.assertEqual(1, len(deployments))
        first_deployment = deployments[0]
        self.assertEqual(environment1['id'],
                         first_deployment['environment_id'])

    @decorators.idempotent_id('d6fbba34-92a9-49b3-9c49-e4b7a65eb6e8')
    def test_list_deployment_statuses(self):
        # Given an environment with a deployment
        environment = self._create_and_deploy_env_session()
        deployment = self.application_catalog_client.list_deployments(
            environment['id'])[0]

        # When list_deployment_statuses is called
        statuses = self.application_catalog_client.list_deployment_statuses(
            environment['id'], deployment['id'])

        # Then the correct statuses for the deployment are returned
        status_deployment_ids = set([s['task_id'] for s in statuses])
        self.assertEqual([deployment['id']], list(status_deployment_ids))
        status_texts = [s['text'] for s in statuses]
        self.assertEqual(['Action deploy is scheduled', 'Deployment finished'],
                         sorted(status_texts))
