# Copyright (c) 2015 OpenStack Foundation.
#
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


import json

import eventlet
try:
    from mistralclient.api import client as mistralcli
except ImportError as mistral_import_error:
    mistralcli = None
from oslo_config import cfg
from oslo_log import log as logging

from murano.common import auth_utils
from murano.dsl import dsl
from murano.dsl import session_local_storage

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class MistralError(Exception):
    pass


@dsl.name('io.murano.system.MistralClient')
class MistralClient(object):
    def __init__(self, this, region_name=None):
        self._owner = this.find_owner('io.murano.Environment')
        self._region_name = region_name

    @property
    def _client(self):
        region = self._region_name or (
            None if self._owner is None else self._owner['region'])
        return self._create_client(region)

    @staticmethod
    @session_local_storage.execution_session_memoize
    def _create_client(region):
        if not mistralcli:
            LOG.warning("Mistral client is not available")
            raise ImportError("Import mistralcliet error")

        mistral_settings = CONF.mistral

        endpoint_type = mistral_settings.endpoint_type
        service_type = mistral_settings.service_type
        session = auth_utils.get_client_session()

        mistral_url = mistral_settings.url or session.get_endpoint(
            service_type=service_type,
            endpoint_type=endpoint_type,
            region_name=region)
        auth_ref = session.auth.get_access(session)

        # TODO(gyurco): use auth_utils.get_session_client_parameters
        return mistralcli.client(
            mistral_url=mistral_url,
            project_id=auth_ref.project_id,
            endpoint_type=endpoint_type,
            service_type=service_type,
            auth_token=auth_ref.auth_token,
            user_id=auth_ref.user_id,
            insecure=mistral_settings.insecure,
            cacert=mistral_settings.cafile
        )

    def upload(self, definition):
        self._client.workflows.create(definition)

    def run(self, name, timeout=600, inputs=None, params=None):
        execution = self._client.executions.create(
            workflow_identifier=name, workflow_input=inputs, params=params)
        # For the fire and forget functionality - when we do not want to wait
        # for the result of the run.
        if timeout == 0:
            return execution.id

        state = execution.state
        try:
            # While the workflow is running we continue to wait until timeout.
            with eventlet.timeout.Timeout(timeout):
                while state not in ('ERROR', 'SUCCESS'):
                    eventlet.sleep(2)
                    execution = self._client.executions.get(execution.id)
                    state = execution.state
        except eventlet.timeout.Timeout:
            error_message = (
                'Mistral run timed out. Execution id: {0}.').format(
                execution.id)
            raise MistralError(error_message)

        if state == 'ERROR':
            error_message = ('Mistral execution completed with ERROR.'
                             ' Execution id: {0}. Output: {1}').format(
                execution.id, execution.output)
            raise MistralError(error_message)

        # Load the JSON we got from Mistral client to dictionary.
        output = json.loads(execution.output)

        # Clean the returned dictionary from unnecessary data.
        # We want to keep only flow level outputs.
        output.pop('openstack', None)
        output.pop('__execution', None)
        output.pop('task', None)

        return output
