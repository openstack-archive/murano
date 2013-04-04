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

import base64
import config
import random
import string
import time

import xml_code_engine


def update_cf_stack(engine, context, body, template,
                    mappings, arguments, **kwargs):
    command_dispatcher = context['/commandDispatcher']

    callback = lambda result: engine.evaluate_content(
        body.find('success'), context)

    command_dispatcher.execute(
        name='cf', command='CreateOrUpdate', template=template,
        mappings=mappings, arguments=arguments, callback=callback)


def delete_cf_stack(engine, context, body, **kwargs):
    command_dispatcher = context['/commandDispatcher']

    callback = lambda result: engine.evaluate_content(
        body.find('success'), context)

    command_dispatcher.execute(
        name='cf', command='Delete', callback=callback)


def prepare_user_data(context, hostname, service, unit,
                      template='Default', **kwargs):
    settings = config.CONF.rabbitmq

    with open('data/init.ps1') as init_script_file:
        with open('data/templates/agent-config/{0}.template'.format(
                template)) as template_file:
            init_script = init_script_file.read()
            template_data = template_file.read()

            replacements = {
                '%RABBITMQ_HOST%': settings.host,
                '%RABBITMQ_INPUT_QUEUE%': '-'.join(
                    [str(context['/dataSource']['name']),
                     str(service), str(unit)]).lower(),
                '%RESULT_QUEUE%': '-execution-results-{0}'.format(
                    str(context['/dataSource']['name'])).lower(),
                '%RABBITMQ_USER%': settings.login,
                '%RABBITMQ_PASSWORD%': settings.password,
                '%RABBITMQ_VHOST%': settings.virtual_host
            }

            template_data = set_config_params(template_data, replacements)

            init_script = init_script.replace(
                '%WINDOWS_AGENT_CONFIG_BASE64%',
                base64.b64encode(template_data))

            init_script = init_script.replace('%INTERNAL_HOSTNAME%', hostname)

            return init_script


def set_config_params(template_data, replacements):
    for key in replacements:
        template_data = template_data.replace(key, replacements[key])
    return template_data


counter = 0


def int2base(x, base):
    digs = string.digits + string.lowercase
    if x < 0:
        sign = -1
    elif x == 0:
        return '0'
    else:
        sign = 1
    x *= sign
    digits = []
    while x:
        digits.append(digs[x % base])
        x /= base
    if sign < 0:
        digits.append('-')
    digits.reverse()
    return ''.join(digits)


def generate_hostname(**kwargs):
    global counter
    prefix = ''.join(random.choice(string.lowercase) for _ in range(5))
    timestamp = int2base(int(time.time() * 1000), 36)[:8]
    suffix = int2base(counter, 36)
    counter = (counter + 1) % 1296
    return prefix + timestamp + suffix


xml_code_engine.XmlCodeEngine.register_function(
    update_cf_stack, "update-cf-stack")

xml_code_engine.XmlCodeEngine.register_function(
    delete_cf_stack, "delete-cf-stack")

xml_code_engine.XmlCodeEngine.register_function(
    prepare_user_data, "prepare-user-data")

xml_code_engine.XmlCodeEngine.register_function(
    generate_hostname, "generate-hostname")
