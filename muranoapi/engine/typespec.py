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

from muranoapi.engine import type_scheme


class PropertyTypes(object):
    In = 'In'
    Out = 'Out'
    InOut = 'InOut'
    Runtime = 'Runtime'
    Const = 'Const'
    All = set([In, Out, InOut, Runtime, Const])
    Writable = set([Out, InOut, Runtime])


class Spec(object):
    def __init__(self, declaration, namespace_resolver):
        self._namespace_resolver = namespace_resolver
        self._contract = type_scheme.TypeScheme(declaration['Contract'])
        self._default = declaration.get('Default')
        self._has_default = 'Default' in declaration
        self._type = declaration.get('Type') or 'In'
        if self._type not in PropertyTypes.All:
            raise SyntaxError('Unknown type {0}. Must be one of ({1})'.format(
                self._type, ', '.join(PropertyTypes.All)))

    def validate(self, value, this, context, object_store, default=None):
        if default is None:
            default = self.default
        return self._contract(value, context, this, object_store,
                              self._namespace_resolver, default)

    @property
    def default(self):
        return self._default

    @property
    def has_default(self):
        return self._has_default

    @property
    def type(self):
        return self._type


class PropertySpec(Spec):
    pass


class ArgumentSpec(Spec):
    pass
