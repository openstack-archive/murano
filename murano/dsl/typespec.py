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

import weakref

from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.dsl import type_scheme


class Spec(object):
    def __init__(self, declaration, container_type):
        self._container_type = weakref.ref(container_type)
        self._contract = type_scheme.TypeScheme(declaration['Contract'])
        self._has_default = 'Default' in declaration
        self._default = declaration.get('Default')

    def transform(self, value, this, owner, context, default=None):
        if default is None:
            default = self.default
        executor = helpers.get_executor(context)
        if isinstance(this, dsl_types.MuranoTypeReference):
            this = this.type
        if isinstance(this, dsl_types.MuranoType):
            return self._contract.transform(
                value, executor.create_object_context(this),
                None, None, default, helpers.get_type(context))
        else:
            return self._contract.transform(
                value, executor.create_object_context(
                    this.cast(self._container_type())),
                this, owner, default, helpers.get_type(context))

    def validate(self, value, context, default=None):
        if default is None:
            default = self.default
        return self._contract.validate(value, context, default)

    @property
    def default(self):
        return self._default

    @property
    def contract(self):
        return self._contract

    @property
    def has_default(self):
        return self._has_default
