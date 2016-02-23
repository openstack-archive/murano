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

import threading
import time

import cloudify_rest_client
import cloudify_rest_client.exceptions as cloudify_exceptions
from murano.dsl import dsl
from oslo_config import cfg as config
from yaql.language import specs
from yaql.language import yaqltypes

import cfg


CONF = config.CONF
archive_upload_lock = threading.Lock()


class CloudifyClient(object):
    @specs.parameter('app', dsl.MuranoObjectParameter('io.murano.Application'))
    def __init__(self, app):
        cloudify_manager = self.CONF.cloudify_manager
        self._client = cloudify_rest_client.CloudifyClient(cloudify_manager)
        self._blueprint_id = '{0}-{1}'.format(app.type.name, app.type.version)
        self._deployment_id = app.id
        self._application_package = app.package

    @specs.parameter('entry_point', yaqltypes.String())
    def publish_blueprint(self, entry_point):
        global archive_upload_lock

        if self._check_blueprint_exists():
            return
        path = self._application_package.get_resource(entry_point)
        with archive_upload_lock:
            try:
                self._client.blueprints.upload(
                    path, self._blueprint_id)
            except cloudify_exceptions.CloudifyClientError as e:
                if e.status_code != 409:
                    raise

    def _check_blueprint_exists(self):
        try:
            self._client.blueprints.get(self._blueprint_id)
            return True
        except cloudify_exceptions.CloudifyClientError as e:
            if e.status_code == 404:
                return False
            raise

    @specs.parameter('parameters', dict)
    def create_deployment(self, parameters=None):
        self._client.deployments.create(
            self._blueprint_id, self._deployment_id, parameters)

    def delete_deployment(self):
        self._client.deployments.delete(self._deployment_id)

    def wait_deployment_ready(self):
        while True:
            executions = self._client.executions.list(self._deployment_id)
            if any(t.status in ('pending', 'started') for t in executions):
                time.sleep(3)
            else:
                deployment = self._client.deployments.get(self._deployment_id)
                return deployment.outputs

    @specs.parameter('name', yaqltypes.String())
    @specs.parameter('parameters', dict)
    def execute_workflow(self, name, parameters=None):
        self._client.executions.start(self._deployment_id, name, parameters)

    @classmethod
    def init_plugin(cls):
        cls.CONF = cfg.init_config(CONF)
