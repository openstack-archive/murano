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


class Spec(object):
    def __init__(self, declaration, namespace_resolver):
        self._namespace_resolver = namespace_resolver
        self._default = declaration.get('Default')
        self._has_default = 'Default' in declaration

    def validate(self, value, this, context, object_store, default=None):
        if default is None:
            default = self.default
        return value if value is not None else default

    @property
    def default(self):
        return self._default

    @property
    def has_default(self):
        return self._has_default


class PropertySpec(Spec):
    pass
