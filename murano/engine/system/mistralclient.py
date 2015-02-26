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

import murano.dsl.helpers as helpers
import murano.dsl.murano_class as murano_class
import murano.dsl.murano_object as murano_object
import murano.openstack.common.log as logging

LOG = logging.getLogger(__name__)


class MistralError(Exception):
    pass


@murano_class.classname('io.murano.system.MistralClient')
class MistralClient(murano_object.MuranoObject):
    def initialize(self, _context):
        self._clients = helpers.get_environment(_context).clients

    def upload(self, _context, definition):
        mistral_client = self._clients.get_mistral_client(_context)
        mistral_client.workflows.update(definition)

    def run(self, _context, name, timeout=600, inputs=None, params=None):
        mistral_client = self._clients.get_mistral_client(_context)
        execution = mistral_client.executions.create(workflow_name=name,
                                                     workflow_input=inputs,
                                                     params=params)
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
                    execution = mistral_client.executions.get(execution.id)
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
