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

from yaql import specs

from murano.dsl import dsl
from murano.dsl import helpers


@dsl.name('io.murano.Object')
class SysObject(object):
    @specs.parameter('owner', dsl.MuranoTypeParameter(nullable=True))
    def set_attr(self, this, context, name, value, owner=None):
        if owner is None:
            owner = helpers.get_type(helpers.get_caller_context(context))

        attribute_store = helpers.get_attribute_store()
        attribute_store.set(this.object, owner, name, value)

    @specs.parameter('owner', dsl.MuranoTypeParameter(nullable=True))
    def get_attr(self, this, context, name, default=None, owner=None):
        if owner is None:
            owner = helpers.get_type(helpers.get_caller_context(context))

        attribute_store = helpers.get_attribute_store()

        result = attribute_store.get(this.object, owner, name)
        return default if result is None else result
