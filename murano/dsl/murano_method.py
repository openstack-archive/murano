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
import types
import weakref

from yaql.language import specs

from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import macros
from murano.dsl import typespec
from murano.dsl import virtual_exceptions
from murano.dsl import yaql_integration


macros.register()
virtual_exceptions.register()


class MethodUsages(object):
    Action = 'Action'
    Runtime = 'Runtime'
    All = set([Action, Runtime])


class MuranoMethod(dsl_types.MuranoMethod):
    def __init__(self, murano_class, name, payload):
        self._name = name
        self._murano_class = weakref.ref(murano_class)

        if callable(payload):
            if isinstance(payload, specs.FunctionDefinition):
                self._body = payload
            else:
                self._body = yaql_integration.get_function_definition(payload)
            self._arguments_scheme = None
            self._usage = (self._body.meta.get('usage') or
                           self._body.meta.get('Usage') or
                           MethodUsages.Runtime)
            if (self._body.name.startswith('#')
                    or self._body.name.startswith('*')):
                raise ValueError(
                    'Import of special yaql functions is forbidden')
        else:
            payload = payload or {}
            self._body = macros.MethodBlock(payload.get('Body') or [], name)
            self._usage = payload.get('Usage') or MethodUsages.Runtime
            arguments_scheme = payload.get('Arguments') or []
            if isinstance(arguments_scheme, types.DictionaryType):
                arguments_scheme = [{key: value} for key, value in
                                    arguments_scheme.iteritems()]
            self._arguments_scheme = collections.OrderedDict()
            for record in arguments_scheme:
                if (not isinstance(record, types.DictionaryType)
                        or len(record) > 1):
                    raise ValueError()
                name = record.keys()[0]
                self._arguments_scheme[name] = typespec.ArgumentSpec(
                    self.name, name, record[name], self.murano_class)
        self._yaql_function_definition = \
            yaql_integration.build_wrapper_function_definition(self)

    @property
    def name(self):
        return self._name

    @property
    def murano_class(self):
        return self._murano_class()

    @property
    def arguments_scheme(self):
        return self._arguments_scheme

    @property
    def yaql_function_definition(self):
        return self._yaql_function_definition

    @property
    def usage(self):
        return self._usage

    @usage.setter
    def usage(self, value):
        self._usage = value

    @property
    def body(self):
        return self._body

    def __repr__(self):
        return 'MuranoMethod({0}::{1})'.format(
            self.murano_class.name, self.name)

    def invoke(self, executor, this, args, kwargs, context=None,
               skip_stub=False):
        if not self.murano_class.is_compatible(this):
            raise Exception("'this' must be of compatible type")
        if isinstance(this, dsl.MuranoObjectInterface):
            this = this.object
        return executor.invoke_method(
            self, this.cast(self.murano_class),
            context, args, kwargs, skip_stub)
