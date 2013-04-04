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

import jsonpath
import re
import types

import function_context
import xml_code_engine


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
        context = function_context.Context()
        context['/dataSource'] = self._data
        context['/commandDispatcher'] = self._command_dispatcher
        context['/config'] = self._config
        context['/reporter'] = self._reporter
        return self._engine.execute(context)

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

        position, match = Workflow._get_relative_position(match, context)
        data = Workflow._get_path(context['/dataSource'], position)
        match = re.sub(r'@\.([\w.]+)',
                       r"Workflow._get_path(@, '\1'.split('.'))", match)
        match = match.replace('$.', '$[*].')
        selected = jsonpath.jsonpath([data], match, 'IPATH') or []
        index = 0
        for found_match in selected:
            if 0 < int(limit) <= index:
                break
            index += 1
            new_position = position + found_match[1:]
            context['__dataSource_currentPosition'] = new_position
            context['__dataSource_currentObj'] = Workflow._get_path(
                context['/dataSource'], new_position)
            for element in body:
                if element.tag == 'empty':
                    continue
                engine.evaluate(element, context)
                if element.tag == 'rule' and context['/hasSideEffects']:
                    break
        if not index:
            empty_handler = body.find('empty')
            if empty_handler is not None:

                engine.evaluate_content(empty_handler, context)


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
