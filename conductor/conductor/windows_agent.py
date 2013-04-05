# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import xml_code_engine

from openstack.common import log as logging
log = logging.getLogger(__name__)


def send_command(engine, context, body, template, service, host, mappings=None,
                 result=None, **kwargs):
    if not mappings:
        mappings = {}
    command_dispatcher = context['/commandDispatcher']

    def callback(result_value):
        log.info(
            'Received result from {2} for {0}: {1}'.format(
                template, result_value, host))
        if result is not None:
            context[result] = result_value['Result']

        success_handler = body.find('success')
        if success_handler is not None:
            engine.evaluate_content(success_handler, context)

    command_dispatcher.execute(
        name='agent', template=template, mappings=mappings,
        host=host, service=service, callback=callback)


xml_code_engine.XmlCodeEngine.register_function(send_command, "send-command")