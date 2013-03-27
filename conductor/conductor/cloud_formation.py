import base64

import xml_code_engine
import config
from random import choice
import time
import string

def update_cf_stack(engine, context, body, template,
                    mappings, arguments, **kwargs):
    command_dispatcher = context['/commandDispatcher']
    print "update-cf", template

    callback = lambda result: engine.evaluate_content(
        body.find('success'), context)

    command_dispatcher.execute(
        name='cf', command='CreateOrUpdate', template=template,
        mappings=mappings, arguments=arguments, callback=callback)

def delete_cf_stack(engine, context, body, **kwargs):
    command_dispatcher = context['/commandDispatcher']
    print "delete-cf"

    callback = lambda result: engine.evaluate_content(
        body.find('success'), context)

    command_dispatcher.execute(
        name='cf', command='Delete', callback=callback)


def prepare_user_data(context, hostname, service, unit, template='Default', **kwargs):
    settings = config.CONF.rabbitmq

    with open('data/init.ps1') as init_script_file:
        with open('data/templates/agent-config/%s.template'
                % template) as template_file:
            init_script = init_script_file.read()
            template_data = template_file.read()
            template_data = template_data.replace(
                '%RABBITMQ_HOST%', settings.host)
            template_data = template_data.replace(
                '%RABBITMQ_INPUT_QUEUE%',
                '-'.join([str(context['/dataSource']['id']),
                         str(service), str(unit)]).lower()
            )
            template_data = template_data.replace(
                '%RESULT_QUEUE%',
                '-execution-results-%s' %
                    str(context['/dataSource']['id']).lower())

            init_script = init_script.replace(
                '%WINDOWS_AGENT_CONFIG_BASE64%',
                base64.b64encode(template_data))

            init_script = init_script.replace('%INTERNAL_HOSTNAME%', hostname)

            return init_script

counter = 0

def int2base(x, base):
    digs = string.digits + string.lowercase
    if x < 0: sign = -1
    elif x==0: return '0'
    else: sign = 1
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
    prefix = ''.join(choice(string.lowercase) for _ in range(5))
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
