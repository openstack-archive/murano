import xml_code_engine

def send_command(engine, context, body, template, mappings, host, **kwargs):
    command_dispatcher = context['/commandDispatcher']

    def callback(result):
        print "Received ", result
        engine.evaluate_content(body.find('success'), context)

    command_dispatcher.execute(name='agent', template=template, mappings=mappings, host=host, callback=callback)


xml_code_engine.XmlCodeEngine.register_function(send_command, "send-command")