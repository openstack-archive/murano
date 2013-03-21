import xml_code_engine


def send_command(engine, context, body, template, host, mappings=None,
                 result=None, **kwargs):
    if not mappings: mappings = {}
    command_dispatcher = context['/commandDispatcher']

    def callback(result_value):
        print "Received result for %s: %s. Body is %s" % \
              (template, result_value, body)
        if result is not None:
            context[result] = result_value['Result']

        success_handler = body.find('success')
        if success_handler is not None:
            engine.evaluate_content(success_handler, context)

    command_dispatcher.execute(name='agent',
        template=template, mappings=mappings,
        host=host, callback=callback)


xml_code_engine.XmlCodeEngine.register_function(send_command, "send-command")