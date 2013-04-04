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

import xml.etree.ElementTree as etree
import types

import function_context


class XmlCodeEngine(object):
    _functionMap = {}

    def __init__(self):
        self._document = None

    def load(self, file_obj):
        self._document = etree.parse(file_obj)

    @staticmethod
    def register_function(func, name):
        XmlCodeEngine._functionMap[name] = func

    def _execute_function(self, name, element, parent_context):
        if name == 'parameter':
            return None

        if name not in self._functionMap:
            raise KeyError('Unknown function %s' % name)

        definition = self._functionMap[name]
        context = function_context.Context(parent_context)
        args = {'engine': self, 'body': element, 'context': context}

        for key, value in element.items():
            args[key] = value

        for parameter in element.findall('parameter'):
            args[parameter.get('name')] = self.evaluate_content(
                parameter, context)

        return definition(**args)

    def evaluate(self, element, parent_context):
        return self._execute_function(element.tag, element, parent_context)

    def evaluate_content(self, element, context):
        parts = [element.text or '']
        do_strip = False
        for sub_element in element:
            if sub_element.tag == 'parameter':
                continue
            do_strip = True
            parts.append(self._execute_function(
                sub_element.tag, sub_element, context))
            parts.append(sub_element.tail or '')

        result = []

        for t in parts:
            if not isinstance(t, types.StringTypes):
                result.append(t)

        return_value = result
        if len(result) == 0:
            return_value = ''.join(parts)
            if do_strip:
                return_value = return_value.strip()
        elif len(result) == 1:
            return_value = result[0]

        return return_value

    def execute(self, parent_context=None):
        root = self._document.getroot()
        return self.evaluate(root, parent_context)


def _dict_func(engine, body, context, **kwargs):
    result = {}
    for item in body:
        key = item.get('name')
        value = engine.evaluate_content(item, context)
        result[key] = value
    return result


def _array_func(engine, body, context, **kwargs):
    result = []
    for item in body:
        result.append(engine.evaluate(item, context))
    return result


def _text_func(engine, body, context, **kwargs):
    return str(engine.evaluate_content(body, context))


def _int_func(engine, body, context, **kwargs):
    return int(engine.evaluate_content(body, context))


def _function_func(engine, body, context, **kwargs):
    return lambda: engine.evaluate_content(body, context)


def _null_func(**kwargs):
    return None


def _true_func(**kwargs):
    return True


def _false_func(**kwargs):
    return False


XmlCodeEngine.register_function(_dict_func, "map")
XmlCodeEngine.register_function(_array_func, "list")
XmlCodeEngine.register_function(_text_func, "text")
XmlCodeEngine.register_function(_int_func, "int")
XmlCodeEngine.register_function(_function_func, "function")
XmlCodeEngine.register_function(_null_func, "null")
XmlCodeEngine.register_function(_true_func, "true")
XmlCodeEngine.register_function(_false_func, "false")
