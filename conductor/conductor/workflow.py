import jsonpath
import types
import re

import xml_code_engine
import function_context

class Workflow(object):
    def __init__(self, filename, data, command_dispatcher, config):
        self._data = data
        self._engine = xml_code_engine.XmlCodeEngine()
        with open(filename) as xml:
            self._engine.load(xml)
        self._command_dispatcher = command_dispatcher
        self._config = config

    def execute(self):
        while True:
            context = function_context.Context()
            context['/dataSource'] = self._data
            context['/commandDispatcher'] = self._command_dispatcher
            context['/config'] = self._config
            if not self._engine.execute(context):
                break

    @staticmethod
    def _get_path(obj, path, create_non_existing=False):
        current = obj
        for part in path:
            if isinstance(current, types.ListType):
                current = current[int(part)]
            elif isinstance(current, types.DictionaryType):
                if part not in current:
                    if create_non_existing:
                        current[part] = {}
                    else:
                        return None
                current = current[part]
            else:
                raise ValueError()

        return current

    @staticmethod
    def _set_path(obj, path, value):
        current = Workflow._get_path(obj, path[:-1], True)
        if isinstance(current, types.ListType):
            current[int(path[-1])] = value
        elif isinstance(current, types.DictionaryType):
            current[path[-1]] = value
        else:
            raise ValueError()

    @staticmethod
    def _select_func(path, context, **kwargs):
        if path.startswith('##'):
            config = context['/config']
            return config[path[2:]]
        elif path.startswith('#'):
            return context[path[1:]]

        position = context['dataSource_currentPosition'] or []
        data = context['dataSource']
        
        index = 0
        for c in path:
            if c == ':':
                if len(position) > 0:
                    position = position[:-1]
            elif c == '/':
                position = []
            else:
                break
            
            index += 1
            
        return Workflow._get_path(data, position + path[index:].split('.'))

    @staticmethod
    def _set_func(path, context, body, engine, **kwargs):
        body_data = engine.evaluate_content(body, context)
        
        if path[0] == '#':
            context[path[1:]] = body_data
            return 

        position = context['dataSource_currentPosition'] or []
        data = context['dataSource']

        index = 0
        for c in path:
            if c == ':':
                if len(position) > 0:
                    position = position[:-1]
            elif c == '/':
                position = []
            else:
                break

            index += 1

        new_position = position + path[index:].split('.')
        if Workflow._get_path(data, new_position) != body_data:
            Workflow._set_path(data, new_position, body_data)
            context['/hasSideEffects'] = True

    @staticmethod
    def _rule_func(match, context, body, engine, limit = 0, **kwargs):
        position = context['dataSource_currentPosition'] or []
        data = context['dataSource_currentObj']
        if data is None:
            data = context['dataSource']
        match = re.sub(r'@\.([\w.]+)', r"Workflow._get_path(@, '\1'.split('.'))", match)
        selected = jsonpath.jsonpath(data, match, 'IPATH') or []

        index = 0
        for found_match in selected:
            if 0 < int(limit) <= index:
                break
            index += 1
            new_position = position + found_match
            context['dataSource_currentPosition'] = new_position
            context['dataSource_currentObj'] = Workflow._get_path(context['dataSource'], new_position)
            for element in body:
                engine.evaluate(element, context)
                if element.tag == 'rule' and context['/hasSideEffects']:
                    break

    @staticmethod
    def _workflow_func(context, body, engine, **kwargs):
        context['/hasSideEffects'] = False
        for element in body:
            engine.evaluate(element, context)
            if element.tag == 'rule' and context['/hasSideEffects']:
                return True
        return False


xml_code_engine.XmlCodeEngine.register_function(Workflow._rule_func, 'rule')
xml_code_engine.XmlCodeEngine.register_function(Workflow._workflow_func, 'workflow')
xml_code_engine.XmlCodeEngine.register_function(Workflow._set_func, 'set')
xml_code_engine.XmlCodeEngine.register_function(Workflow._select_func, 'select')
