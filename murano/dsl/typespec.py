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

from murano.dsl.contracts import contracts
from murano.dsl import dsl_types
from murano.dsl import helpers


class Spec(object):
    def __init__(self, declaration, container_type):
        self._container_type = weakref.ref(container_type)
        self._contract = contracts.Contract(
            declaration['Contract'], container_type)
        self._has_default = 'Default' in declaration
        self._default = declaration.get('Default')

    def _get_this_context(self, this):
        executor = helpers.get_executor()
        if isinstance(this, dsl_types.MuranoType):
            return executor.create_object_context(this)
        return executor.create_object_context(
            this.cast(self._container_type()))

    def transform(self, value, this, owner, context, default=None,
                  finalize=True):
        if default is None:
            default = self.default
        if isinstance(this, dsl_types.MuranoTypeReference):
            this = this.type
        if isinstance(this, dsl_types.MuranoType):
            return self._contract.transform(
                value, self._get_this_context(this),
                None, None, default, helpers.get_type(context),
                finalize=finalize)
        else:
            return self._contract.transform(
                value, self._get_this_context(this),
                this, owner, default, helpers.get_type(context),
                finalize=finalize)

    def validate(self, value, this, context, default=None):
        if default is None:
            default = self.default
        return self._contract.validate(
            value, self._get_this_context(this), default,
            helpers.get_type(context))

    def check_type(self, value, context, default=None):
        if default is None:
            default = self.default
        return self._contract.check_type(
            value, context, default, helpers.get_type(context))

    def finalize(self, value, this, context):
        return self._contract.finalize(
            value, self._get_this_context(this), helpers.get_type(context))

    @property
    def default(self):
        return self._default

    @property
    def contract(self):
        return self._contract

    @property
    def has_default(self):
        return self._has_default

    @property
    def declaring_type(self):
        return self._container_type()
