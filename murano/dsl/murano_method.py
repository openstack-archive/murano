#    Copyright (c) 2014 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import collections
import inspect
import types

import murano.dsl.macros as macros
import murano.dsl.typespec as typespec
import murano.dsl.virtual_exceptions as virtual_exceptions
import murano.dsl.yaql_expression as yaql_expression


macros.register()
virtual_exceptions.register()


class MethodUsages(object):
    Action = 'Action'
    Runtime = 'Runtime'
    All = set([Action, Runtime])


def methodusage(usage):
    def wrapper(method):
        method._murano_method_usage = usage
        return method
    return wrapper


class MuranoMethod(object):
    def __init__(self, murano_class, name, payload):
        self._name = name
        self._murano_class = murano_class

        if callable(payload):
            self._body = payload
            self._arguments_scheme = self._generate_arguments_scheme(payload)
            self._usage = getattr(payload, '_murano_method_usage',
                                  MethodUsages.Runtime)
        else:
            payload = payload or {}
            self._body = self._prepare_body(payload.get('Body') or [], name)
            self._usage = payload.get('Usage') or MethodUsages.Runtime
            arguments_scheme = payload.get('Arguments') or []
            if isinstance(arguments_scheme, types.DictionaryType):
                arguments_scheme = [{key: value} for key, value in
                                    arguments_scheme.iteritems()]
            self._arguments_scheme = collections.OrderedDict()
            for record in arguments_scheme:
                if not isinstance(record, types.DictionaryType) \
                        or len(record) > 1:
                    raise ValueError()
                name = record.keys()[0]
                self._arguments_scheme[name] = typespec.ArgumentSpec(
                    record[name], murano_class)

    @property
    def name(self):
        return self._name

    @property
    def murano_class(self):
        return self._murano_class

    @property
    def arguments_scheme(self):
        return self._arguments_scheme

    @property
    def usage(self):
        return self._usage

    @property
    def body(self):
        return self._body

    def _generate_arguments_scheme(self, func):
        func_info = inspect.getargspec(func)
        data = [(name, {'Contract': yaql_expression.YaqlExpression('$')})
                for name in func_info.args]
        if inspect.ismethod(func):
            data = data[1:]
        defaults = func_info.defaults or tuple()
        for i in xrange(len(defaults)):
            data[i + len(data) - len(defaults)][1]['Default'] = defaults[i]
        result = collections.OrderedDict([
            (name, typespec.ArgumentSpec(declaration, self.murano_class))
            for name, declaration in data])
        if '_context' in result:
            del result['_context']
        return result

    def _prepare_body(self, body, name):
        return macros.MethodBlock(body, name)

    def __repr__(self):
        return 'MuranoMethod({0}::{1})'.format(
            self.murano_class.name, self.name)

    def invoke(self, executor, this, parameters):
        return self.murano_class.invoke(self.name, executor, this, parameters)
