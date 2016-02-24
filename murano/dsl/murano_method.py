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
import sys
import weakref

import six
from yaql.language import specs

from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import macros
from murano.dsl import typespec
from murano.dsl import virtual_exceptions
from murano.dsl import yaql_integration


macros.register()
virtual_exceptions.register()


class MethodUsages(object):
    Action = 'Action'
    Runtime = 'Runtime'
    Static = 'Static'
    All = set([Action, Runtime, Static])


class MuranoMethod(dsl_types.MuranoMethod):
    def __init__(self, murano_class, name, payload, original_name=None):
        self._name = name
        original_name = original_name or name
        self._murano_class = weakref.ref(murano_class)

        if callable(payload):
            if isinstance(payload, specs.FunctionDefinition):
                self._body = payload
            else:
                self._body = yaql_integration.get_function_definition(
                    payload, weakref.proxy(self), original_name)
            self._arguments_scheme = None
            if any((
                helpers.inspect_is_static(
                    murano_class.extension_class, original_name),
                helpers.inspect_is_classmethod(
                    murano_class.extension_class, original_name))):
                self._usage = MethodUsages.Static
            else:
                self._usage = (self._body.meta.get('usage') or
                               self._body.meta.get('Usage') or
                               MethodUsages.Runtime)
            if (self._body.name.startswith('#') or
                    self._body.name.startswith('*')):
                raise ValueError(
                    'Import of special yaql functions is forbidden')
        else:
            payload = payload or {}
            self._body = macros.MethodBlock(payload.get('Body') or [], name)
            self._usage = payload.get('Usage') or MethodUsages.Runtime
            arguments_scheme = payload.get('Arguments') or []
            if isinstance(arguments_scheme, dict):
                arguments_scheme = [{key: value} for key, value in
                                    six.iteritems(arguments_scheme)]
            self._arguments_scheme = collections.OrderedDict()
            for record in arguments_scheme:
                if (not isinstance(record, dict) or
                        len(record) > 1):
                    raise ValueError()
                name = list(record.keys())[0]
                self._arguments_scheme[name] = MuranoMethodArgument(
                    self, self.name, name, record[name])
        self._yaql_function_definition = \
            yaql_integration.build_wrapper_function_definition(
                weakref.proxy(self))

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

    @property
    def is_static(self):
        return self.usage == MethodUsages.Static

    def __repr__(self):
        return 'MuranoMethod({0}::{1})'.format(
            self.murano_class.name, self.name)

    def invoke(self, executor, this, args, kwargs, context=None,
               skip_stub=False):
        if isinstance(this, dsl.MuranoObjectInterface):
            this = this.object
        if this and not self.murano_class.is_compatible(this):
            raise Exception("'this' must be of compatible type")
        if not this and not self.is_static:
            raise Exception("A class instance is required")

        if isinstance(this, dsl_types.MuranoObject):
            this = this.cast(self.murano_class)
        else:
            this = self.murano_class
        return executor.invoke_method(
            self, this, context, args, kwargs, skip_stub)


class MuranoMethodArgument(dsl_types.MuranoMethodArgument, typespec.Spec):
    def __init__(self, murano_method, method_name, arg_name, declaration):
        super(MuranoMethodArgument, self).__init__(
            declaration, murano_method.murano_class)
        self._method_name = method_name
        self._arg_name = arg_name
        self._murano_method = weakref.ref(murano_method)

    def validate(self, *args, **kwargs):
        try:
            return super(MuranoMethodArgument, self).validate(*args, **kwargs)
        except exceptions.ContractViolationException as e:
            msg = u'[{0}::{1}({2}{3})] {4}'.format(
                self.murano_method.murano_class.name,
                self.murano_method.name, self.name,
                e.path, six.text_type(e))
            six.reraise(exceptions.ContractViolationException,
                        msg, sys.exc_info()[2])

    @property
    def murano_method(self):
        return self._murano_method()

    @property
    def name(self):
        return self._arg_name

    def __repr__(self):
        return 'MuranoMethodArgument({method}::{name})'.format(
            method=self.murano_method.name, name=self.name)
