import base64

import xml_code_engine
import config
from random import choice
import time

def update_cf_stack(engine, context, body, template,
                    mappings, arguments, **kwargs):
    command_dispatcher = context['/commandDispatcher']
    print "update-cf", template

    callback = lambda result: engine.evaluate_content(
        body.find('success'), context)

    command_dispatcher.execute(
        name='cf', template=template, mappings=mappings,
        arguments=arguments, callback=callback)


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
                         str(service), str(unit)])
            )
            template_data = template_data.replace(
                '%RESULT_QUEUE%',
                '-execution-results-%s' % str(context['/dataSource']['id']))

            init_script = init_script.replace(
                '%WINDOWS_AGENT_CONFIG_BASE64%',
                base64.b64encode(template_data))

            init_script = init_script.replace('%INTERNAL_HOSTNAME%', hostname)

            return init_script

def generate_hostname(**kwargs):
    chars = 'abcdefghijklmnopqrstuvwxyz'
    prefix = ''.join(choice(chars) for _ in range(4))
    return prefix + str(int(time.time() * 10))




xml_code_engine.XmlCodeEngine.register_function(
    update_cf_stack, "update-cf-stack")

xml_code_engine.XmlCodeEngine.register_function(
    prepare_user_data, "prepare-user-data")

xml_code_engine.XmlCodeEngine.register_function(
    generate_hostname, "generate-hostname")
