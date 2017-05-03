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
import os

from tempest import config
from tempest.lib.common import rest_client

from murano_tempest_tests import utils

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
        parsed = self._parse_resp(body)
        return parsed['artifacts']

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
        uri = 'v0.1/artifacts/murano/v1/drafts'
        kwargs.update({'name': name, 'version': version})
        resp, body = self.post(uri, body=json.dumps(kwargs))
        self.expected_success(201, resp.status)
        return self._parse_resp(body)

    def publish_artifact(self, artifact_id):
        uri = 'v0.1/artifacts/murano/v1/{0}/publish'.format(artifact_id)
        resp, body = self.post(uri, body='')
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
        self.expected_success(204, resp.status)
        return self._parse_resp(body)

    def upload_blob(self, artifact_id, blob_type, data):
        headers = {'Content-Type': 'application/octet-stream'}
        uri = 'v0.1/artifacts/murano/v1/{0}/{1}'.format(
            artifact_id, blob_type)
        resp, body = self.put(uri, data, headers=headers)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

    def download_blob(self, artifact_id, blob_type):
        uri = 'v0.1/artifacts/murano/v1/{0}/{1}/download'.format(
            artifact_id, blob_type)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        return self._parse_resp(body)

# -----------------------------Packages methods-------------------------------

    def get_list_packages(self):
        return self.list_artifacts()

    def delete_package(self, package_id):
        return self.delete_artifact(package_id)

    def upload_package(self, package_name, package_path, top_dir, body):
        files = {package_name: open(os.path.join(top_dir, package_path), 'rb')}
        is_public = body.pop('is_public', None)
        if is_public is not None:
            body['visibility'] = 'public' if is_public else 'private'
        fqn = list(files.keys())[0]
        package = utils.Package.from_file(files[fqn])
        manifest = package.manifest
        package_draft = {
            'name': manifest.get('FullName', fqn),
            'version': manifest.get('Version', '0.0.0'),
            'description': manifest.get('Description'),
            'display_name': manifest.get('Name', fqn),
            'type': manifest.get('Type', 'Application'),
            'author': manifest.get('Author'),
            'tags': manifest.get('Tags', []),
            'class_definitions': package.classes.keys()
        }
        for k, v in body.items():
            package_draft[k] = v

        inherits = utils.get_local_inheritance(package.classes)

        # TODO(kzaitsev): add local and global inheritance information tests
        package_draft['inherits'] = inherits

        keywords = package_draft['tags']
        package_draft['keywords'] = keywords

        draft = self.create_artifact_draft(**package_draft)
        self.upload_blob(draft['id'], 'archive', package.file())

        # TODO(kzaitsev): add logo upload code, currently it's failing for me
        # with io.UnsupportedOperation: fileno

        # if package.logo is not None:
        #     self.upload_blob(draft['id'], 'logo', package.logo)
        # if package.ui is not None:
        #     self.client.artifacts.upload_blob(draft['id'], 'ui_definition',
        #                                       package.ui)
        self.publish_artifact(draft['id'])
        return draft
