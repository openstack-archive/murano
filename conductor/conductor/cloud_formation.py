import xml_code_engine

def update_cf_stack(engine, context, body, template, mappings, arguments, **kwargs):
    command_dispatcher = context['/commandDispatcher']

    callback = lambda result: engine.evaluate_content(body.find('success'), context)
    command_dispatcher.execute(name='cf', template=template, mappings=mappings, arguments=arguments, callback=callback)


xml_code_engine.XmlCodeEngine.register_function(update_cf_stack, "update-cf-stack")