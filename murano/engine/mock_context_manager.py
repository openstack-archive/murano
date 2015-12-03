# Copyright (c) 2015 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from murano.common import engine
from murano.dsl import linked_context
from murano.dsl import yaql_integration


class MockContextManager(engine.ContextManager):

    def __init__(self):
        # { object_id: [mock_function_definitions] }
        self.obj_mock_ctx = {}

        # { class_name: [mock_function_definitions] }
        self.class_mock_ctx = {}

    def _create_new_ctx(self, mock_funcs):
        mock_context = yaql_integration.create_empty_context()
        for mock_func in mock_funcs:
            mock_context.register_function(mock_func)
        return mock_context

    def _create_new_ctx_for_class(self, name):
        new_context = None
        if name in self.class_mock_ctx:
            new_context = self._create_new_ctx(self.class_mock_ctx[name])
        return new_context

    def _create_new_ctx_for_obj(self, obj_id):
        new_context = None
        if obj_id in self.obj_mock_ctx:
            new_context = self._create_new_ctx(self.obj_mock_ctx[obj_id])
        return new_context

    def create_class_context(self, murano_class):
        original_context = super(MockContextManager,
                                 self).create_class_context(murano_class)

        mock_context = self._create_new_ctx_for_class(murano_class.name)
        if mock_context:
            result_context = linked_context.link(
                original_context, mock_context).create_child_context()
        else:
            result_context = original_context
        return result_context

    def create_object_context(self, murano_obj):
        original_context = super(MockContextManager,
                                 self).create_object_context(murano_obj)

        mock_context = self._create_new_ctx_for_obj(murano_obj.type.name)
        if mock_context:
            result_context = linked_context.link(
                original_context, mock_context).create_child_context()
        else:
            result_context = original_context
        return result_context
