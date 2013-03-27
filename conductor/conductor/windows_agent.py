import xml_code_engine

from openstack.common import log as logging
log = logging.getLogger(__name__)


def send_command(engine, context, body, template, service, host, mappings=None,
                 result=None, **kwargs):
    if not mappings: mappings = {}
    command_dispatcher = context['/commandDispatcher']

    def callback(result_value):
        log.info('Received result from {3} for {0}: {1}. Body is {2}'.format(
              template, result_value, body, host))
        if result is not None:
            context[result] = result_value['Result']

        success_handler = body.find('success')
        if success_handler is not None:
            engine.evaluate_content(success_handler, context)

    command_dispatcher.execute(name='agent',
        template=template, mappings=mappings,
        host=host, service=service, callback=callback)


xml_code_engine.XmlCodeEngine.register_function(send_command, "send-command")