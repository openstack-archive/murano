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

from yaql.language import specs
from yaql.language import yaqltypes

from murano.common import engine
from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import helpers
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

    def create_type_context(self, murano_type):
        original_context = super(
            MockContextManager, self).create_type_context(murano_type)

        mock_context = self._create_new_ctx_for_class(murano_type.name)
        if mock_context:
            result_context = helpers.link_contexts(
                original_context, mock_context).create_child_context()
        else:
            result_context = original_context
        return result_context

    def create_object_context(self, murano_obj):
        original_context = super(
            MockContextManager, self).create_object_context(murano_obj)

        mock_context = self._create_new_ctx_for_obj(murano_obj.type.name)
        if mock_context:
            result_context = helpers.link_contexts(
                original_context, mock_context).create_child_context()
        else:
            result_context = original_context
        return result_context

    def create_root_context(self, runtime_version):
        root_context = super(MockContextManager, self).create_root_context(
            runtime_version)
        constext = root_context.create_child_context()
        constext.register_function(inject_method_with_str, name='inject')
        constext.register_function(inject_method_with_yaql_expr,
                                   name='inject')
        constext.register_function(with_original)
        return constext


@specs.parameter('kwargs', yaqltypes.Lambda(with_context=True))
def with_original(context, **kwargs):
    new_context = context.create_child_context()

    original_context = context[constants.CTX_ORIGINAL_CONTEXT]
    for k, v in kwargs.items():
        new_context['$' + k] = v(original_context)
    return new_context


@specs.parameter(
    'target',
    yaqltypes.AnyOf(dsl.MuranoTypeParameter(), dsl.MuranoObjectParameter()))
@specs.parameter('target_method', yaqltypes.String())
@specs.parameter('mock_object', dsl.MuranoObjectParameter())
@specs.parameter('mock_name', yaqltypes.String())
def inject_method_with_str(context, target, target_method,
                           mock_object, mock_name):
    ctx_manager = helpers.get_executor().context_manager

    current_class = helpers.get_type(context)
    mock_func = current_class.find_single_method(mock_name)
    original_class = target.type

    original_function = original_class.find_single_method(target_method)
    result_fd = original_function.instance_stub.clone()

    def payload_adapter(__context, __sender, *args, **kwargs):
        return mock_func.invoke(
            mock_object, args, kwargs, __context, True)

    result_fd.payload = payload_adapter
    existing_mocks = ctx_manager.class_mock_ctx.setdefault(
        original_class.name, [])
    existing_mocks.append(result_fd)


@specs.parameter(
    'target',
    yaqltypes.AnyOf(dsl.MuranoTypeParameter(), dsl.MuranoObjectParameter()))
@specs.parameter('target_method', yaqltypes.String())
@specs.parameter('expr', yaqltypes.Lambda(with_context=True))
def inject_method_with_yaql_expr(context, target, target_method, expr):
    ctx_manager = helpers.get_executor().context_manager
    original_class = target.type

    original_function = original_class.find_single_method(target_method)
    result_fd = original_function.instance_stub.clone()

    def payload_adapter(__super, __context, __sender, *args, **kwargs):
        new_context = context.create_child_context()
        new_context[constants.CTX_ORIGINAL_CONTEXT] = __context
        mock_obj = context[constants.CTX_THIS]
        new_context.register_function(lambda: __super(*args, **kwargs),
                                      name='originalMethod')
        return expr(new_context, mock_obj, *args, **kwargs)

    result_fd.payload = payload_adapter
    result_fd.insert_parameter('__super', yaqltypes.Super())
    existing_mocks = ctx_manager.class_mock_ctx.setdefault(
        original_class.name, [])
    existing_mocks.append(result_fd)
