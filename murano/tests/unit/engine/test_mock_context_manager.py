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

from murano.dsl import murano_class
from murano.engine import mock_context_manager
from murano.tests.unit import base

FIXTURE_CLASS = 'io.murano.system.Agent'
FIXTURE_FUNC = 'call'


def _get_fd(set_to_extract):
    return list(set_to_extract)[0]


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
