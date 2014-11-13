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

from murano.dsl import exceptions
import murano.dsl.type_scheme as type_scheme


class PropertyUsages(object):
    In = 'In'
    Out = 'Out'
    InOut = 'InOut'
    Runtime = 'Runtime'
    Const = 'Const'
    Config = 'Config'
    All = set([In, Out, InOut, Runtime, Const, Config])
    Writable = set([Out, InOut, Runtime])


class Spec(object):
    def __init__(self, declaration, owner_class):
        self._namespace_resolver = owner_class.namespace_resolver
        self._contract = type_scheme.TypeScheme(declaration['Contract'])
        self._usage = declaration.get('Usage') or 'In'
        self._default = declaration.get('Default')
        self._has_default = 'Default' in declaration
        if self._usage not in PropertyUsages.All:
            raise exceptions.DslSyntaxError(
                'Unknown type {0}. Must be one of ({1})'.format(
                    self._usage, ', '.join(PropertyUsages.All)))

    def validate(self, value, this, owner, context,
                 object_store, default=None):
        if default is None:
            default = self.default
        return self._contract(value, context, this, owner, object_store,
                              self._namespace_resolver, default)

    @property
    def default(self):
        return self._default

    @property
    def has_default(self):
        return self._has_default

    @property
    def usage(self):
        return self._usage


class PropertySpec(Spec):
    pass


class ArgumentSpec(Spec):
    pass
