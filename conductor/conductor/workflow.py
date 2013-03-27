import jsonpath
import types
import re

import xml_code_engine
import function_context


class Workflow(object):
    def __init__(self, filename, data, command_dispatcher, config, reporter):
        self._data = data
        self._engine = xml_code_engine.XmlCodeEngine()
        with open(filename) as xml:
            self._engine.load(xml)
        self._command_dispatcher = command_dispatcher
        self._config = config
        self._reporter = reporter

    def execute(self):
        while True:
            context = function_context.Context()
            context['/dataSource'] = self._data
            context['/commandDispatcher'] = self._command_dispatcher
            context['/config'] = self._config
            context['/reporter'] = self._reporter
            if not self._engine.execute(context):
                break

    @staticmethod
    def _get_path(obj, path, create_non_existing=False):
        # result = jsonpath.jsonpath(obj, '.'.join(path))
        # if not result or len(result) < 1:
        #     return None
        # return result[0]
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
    def _get_relative_position(path, context):
        position = context['__dataSource_currentPosition'] or []

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

        return position, path[index:]

    @staticmethod
    def _correct_position(path, context):
        position, suffix = Workflow._get_relative_position(path, context)

        if not suffix:
            return position
        else:
            return position + suffix.split('.')

    @staticmethod
    def _select_func(context, path='', source=None, **kwargs):

        if path.startswith('##'):
            config = context['/config']
            return config[path[2:]]
        elif path.startswith('#'):
            return context[path[1:]]

        if source is not None:
            return Workflow._get_path(
                context[source], path.split('.'))
        else:
            return Workflow._get_path(
                context['/dataSource'],
                Workflow._correct_position(path, context))

    @staticmethod
    def _set_func(path, context, body, engine, target=None, **kwargs):
        body_data = engine.evaluate_content(body, context)

        if path.startswith('##'):
            raise RuntimeError('Cannot modify config from XML-code')
        elif path.startswith('#'):
            context[':' + path[1:]] = body_data
            return

        if target:
            data = context[target]
            position = path.split('.')
            if Workflow._get_path(data, position) != body_data:
                Workflow._set_path(data, position, body_data)
                context['/hasSideEffects'] = True
        else:
            data = context['/dataSource']
            new_position = Workflow._correct_position(path, context)
            if Workflow._get_path(data, new_position) != body_data:
                Workflow._set_path(data, new_position, body_data)
                context['/hasSideEffects'] = True

    @staticmethod
    def _rule_func(match, context, body, engine, limit=0, name=None, **kwargs):
        position = context['__dataSource_currentPosition'] or []

        if name == 'marker':
            print "!"
        # data = context['__dataSource_currentObj']
        # if data is None:
        #     data = context['/dataSource']
        position, match = Workflow._get_relative_position(match, context)
        data = Workflow._get_path(context['/dataSource'], position)
        match = re.sub(r'@\.([\w.]+)',
                       r"Workflow._get_path(@, '\1'.split('.'))", match)
        selected = jsonpath.jsonpath(data, match, 'IPATH') or []

        index = 0
        for found_match in selected:
            if 0 < int(limit) <= index:
                break
            index += 1
            new_position = position + found_match
            context['__dataSource_currentPosition'] = new_position
            context['__dataSource_currentObj'] = Workflow._get_path(
                context['/dataSource'], new_position)
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


xml_code_engine.XmlCodeEngine.register_function(
    Workflow._rule_func, 'rule')

xml_code_engine.XmlCodeEngine.register_function(
    Workflow._workflow_func, 'workflow')

xml_code_engine.XmlCodeEngine.register_function(
    Workflow._set_func, 'set')

xml_code_engine.XmlCodeEngine.register_function(
    Workflow._select_func, 'select')
