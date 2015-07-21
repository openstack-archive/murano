# Copyright (c) 2015 Openstack Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import uuid

import mistralclient.api.client as mistralclient
import testresources
import testtools

import murano.tests.functional.common.tempest_utils as tempest_utils
import murano.tests.functional.common.utils as utils


class MistralIntegration(testtools.TestCase, testtools.testcase.WithAttributes,
                         testresources.ResourcedTestCase,
                         tempest_utils.TempestDeployTestMixin):

    @classmethod
    @utils.memoize
    def mistral_client(cls):
        keystone_client = cls.keystone_client()

        endpoint_type = 'publicURL'
        service_type = 'workflowv2'

        mistral_url = keystone_client.service_catalog.url_for(
            service_type=service_type,
            endpoint_type=endpoint_type)

        auth_token = keystone_client.auth_token

        return mistralclient.client(mistral_url=mistral_url,
                                    auth_url=keystone_client.auth_url,
                                    project_id=keystone_client.tenant_id,
                                    endpoint_type=endpoint_type,
                                    service_type=service_type,
                                    auth_token=auth_token,
                                    user_id=keystone_client.user_id)

    @classmethod
    def upload_mistral_showcase_app(cls):
        app_dir = 'io.murano.apps.test.MistralShowcaseApp'
        zip_file_path = cls.zip_dir(os.path.dirname(__file__), app_dir)
        cls.init_list("_package_files")
        cls._package_files.append(zip_file_path)
        return cls.upload_package(
            'MistralShowcaseApp',
            {"categories": ["Web"], "tags": ["tag"]},
            zip_file_path)

    @staticmethod
    def _create_env_body():
        return {
            "name": "Mistral_environment",
            "?": {
                "type": "io.murano.apps.test.MistralShowcaseApp",
                "id": str(uuid.uuid4())
            }
        }
