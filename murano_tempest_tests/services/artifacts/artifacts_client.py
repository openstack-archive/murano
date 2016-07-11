# Copyright (c) 2016 Mirantis, Inc.
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

import json

from tempest import config
from tempest.lib.common import rest_client

CONF = config.CONF


class ArtifactsClient(rest_client.RestClient):
    """Tempest REST client for Glance Artifacts"""

    def __init__(self, auth_provider):
        super(ArtifactsClient, self).__init__(
            auth_provider,
            CONF.artifacts.catalog_type,
            CONF.identity.region,
            endpoint_type=CONF.artifacts.endpoint_type)
        self.build_interval = CONF.artifacts.build_interval
        self.build_timeout = CONF.artifacts.build_timeout

# -----------------------------Artifacts methods-------------------------------

    def list_artifacts(self):
        uri = 'v0.1/artifacts/murano/v1'
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def list_drafts(self):
        uri = 'v0.1/artifacts/murano/v1/creating'
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def list_deactivated_drafts(self):
        uri = 'v0.1/artifacts/murano/v1/deactivated'
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def create_artifact_draft(self, name, version, **kwargs):
        uri = 'v0.1/artifacts/murano/v1/creating'
        kwargs.update({'name': name, 'version': version})
        resp, body = self.post(uri, body=json.dumps(kwargs))
        self.expected_success(201, resp.status)
        return self._parse_resp(body)

    def publish_artifact(self, artifact_id):
        uri = 'v0.1/artifacts/murano/v1/{0}/publish'.format(artifact_id)
        resp, body = self.post(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def get_artifact(self, artifact_id):
        uri = 'v0.1/artifacts/murano/v1/{0}'.format(artifact_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def update_artifact(self, artifact_id, body):
        headers = {
            'Content-Type': 'application/openstack-images-v2.1-json-patch'}
        uri = 'v0.1/artifacts/murano/v1/{0}'.format(artifact_id)
        resp, body = self.patch(uri, json.dumps(body), headers=headers)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def delete_artifact(self, artifact_id):
        uri = 'v0.1/artifacts/murano/v1/{0}'.format(artifact_id)
        resp, body = self.delete(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def upload_blob(self, artifact_id, blob_type, data):
        headers = {'Content-Type': 'application/octet-stream'}
        uri = 'v0.1/artifacts/murano/v1/{0}/{1}'.format(
            artifact_id, blob_type)
        resp, body = self.put(uri, data, headers=headers)
        self.expected_success(201, resp.status)
        return self._parse_resp(body)

    def download_blob(self, artifact_id, blob_type):
        uri = 'v0.1/artifacts/murano/v1/{0}/{1}/download'.format(
            artifact_id, blob_type)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)
