#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import mock
from yaql import contexts
from yaql import specs

from murano.dsl import constants
from murano.dsl import executor
from murano.dsl import murano_class
from murano.engine import environment
from murano.engine import mock_context_manager
from murano.tests.unit import base
from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import runner
from murano.tests.unit.dsl.foundation import test_case


FIXTURE_CLASS = 'io.murano.system.Agent'
FIXTURE_FUNC = 'call'


def _get_fd(set_to_extract):
    return list(set_to_extract)[0]


class TestMockContextManager(mock_context_manager.MockContextManager):
    def __init__(self, functions):
        super(TestMockContextManager, self).__init__()
        self.__functions = functions

    def create_root_context(self, runtime_version):
        root_context = super(TestMockContextManager, self).create_root_context(
            runtime_version)
        context = root_context.create_child_context()
        for name, func in self.__functions.iteritems():
            context.register_function(func, name)
        return context


class MockRunner(runner.Runner):
    def __init__(self, model, package_loader, functions):
        if isinstance(model, basestring):
            model = om.Object(model)
        model = om.build_model(model)
        if 'Objects' not in model:
            model = {'Objects': model}

        self.executor = executor.MuranoDslExecutor(
            package_loader, TestMockContextManager(functions),
            environment.Environment())
        self._root = self.executor.load(model).object


class TestMockManager(base.MuranoTestCase):

    def test_create_class_context(self):
        mock_manager = mock_context_manager.MockContextManager()
        mock_murano_class = mock.MagicMock(spec=murano_class.MuranoClass)
        mock_murano_class.name = FIXTURE_CLASS
        original_function = mock.MagicMock(spec=specs.FunctionDefinition)
        original_function.is_method = True
        original_function.name = FIXTURE_FUNC
        original_context = contexts.Context()
        p = mock.patch("inspect.getargspec", new=mock.MagicMock())
        p.start()
        original_context.register_function(original_function)
        mock_murano_class.context = original_context
        p.stop()

        mock_function = mock.MagicMock(spec=specs.FunctionDefinition)
        mock_function.is_method = True
        mock_function.name = FIXTURE_FUNC

        mock_manager.class_mock_ctx[FIXTURE_CLASS] = [mock_function]

        result_context = mock_manager.create_class_context(mock_murano_class)
        all_functions = result_context.collect_functions(FIXTURE_FUNC)

        # Mock function should go first, but result context should contain both
        self.assertIs(mock_function, _get_fd(all_functions[0]))
        self.assertIs(original_function, _get_fd(all_functions[1]))

    def test_create_root_context(self):
        mock_manager = mock_context_manager.MockContextManager()
        ctx_to_check = mock_manager.create_root_context(
            constants.RUNTIME_VERSION_1_1)
        inject_count = ctx_to_check.collect_functions('inject')
        with_original_count = ctx_to_check.collect_functions('withOriginal')

        self.assertEqual(2, len(inject_count[0]))
        self.assertEqual(1, len(with_original_count[0]))


class TestMockYaqlFunctions(test_case.DslTestCase):

    def setUp(self):
        super(TestMockYaqlFunctions, self).setUp()
        self.runner = MockRunner(om.Object('TestMocks'),
                                 self.package_loader, self._functions)

    def test_inject_method_with_str(self):
        self.runner.testInjectMethodWithString()
        self.assertEqual(['This is mock1'], self.traces)

    def test_inject_object_with_str(self):
        self.runner.testInjectObjectWithString()
        self.assertEqual(['This is mock1'], self.traces)

    def test_inject_method_with_yaql_expr(self):
        self.runner.testInjectMethodWithYaqlExpr()
        self.assertEqual(['method1', 'I am mock'], self.traces)

    def test_inject_object_with_yaql_expr(self):
        self.runner.testInjectObjectWithYaqlExpr()
        self.assertEqual(['method1', 'I am mock'], self.traces)

    def test_with_original(self):
        self.runner.testWithoriginal()
        self.assertEqual(['DEFAULT'], self.traces)

    def test_original_method(self):
        self.runner.testOriginalMethod()
        self.assertEqual(['method1'], self.traces)
