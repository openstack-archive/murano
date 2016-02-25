#    Copyright (c) 2015 Mirantis, Inc.
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

from murano.dsl import yaql_integration


# noinspection PyMethodMayBeStatic
class ContextManager(object):
    """Context manager for the MuranoDslExecutor.

    DSL hosting project should subclass this and override methods in order
    to insert yaql function at various scopes. For example it may override
    create_root_context to register its own global yaql functions.
    """

    def create_root_context(self, runtime_version):
        return yaql_integration.create_context(runtime_version)

    def create_package_context(self, package):
        return package.context

    def create_type_context(self, murano_type):
        return murano_type.context

    def create_object_context(self, obj):
        return None
