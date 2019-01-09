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
import mock

from murano.dsl import helpers
from murano.dsl import session_local_storage
from murano.tests.unit.dsl.foundation import test_case


class FakeWithInit(session_local_storage._localbase):
    def __init__(self, *args, **kwargs):
        pass


class FakeNoInit(session_local_storage._localbase):
    pass


class TestLocalbase(test_case.DslTestCase):
    def test_new(self):
        lb = FakeWithInit.__new__(
            FakeWithInit, 42, 'foo', bar='baz')
        self.assertEqual(((42, 'foo',), {'bar': 'baz'}), lb._local__args)

    def test_new_bad(self):
        self.assertRaises(
            TypeError, FakeNoInit.__name__)


class TestPatch(test_case.DslTestCase):
    @mock.patch.object(helpers, 'get_execution_session',
                       return_value=mock.sentinel.session)
    def test_patch(self, mock_ges):
        fwi = FakeWithInit(foo='bar')
        session_local_storage._patch(fwi)
        self.assertEqual({}, fwi.__dict__)


class TestLocal(test_case.DslTestCase):
    class FakeLocal(session_local_storage._local):
        def __init__(self, foo):
            self.foo = foo

    @mock.patch.object(session_local_storage, '_patch')
    def setUp(self, mock_patch):
        super(TestLocal, self).setUp()
        self.fl = self.FakeLocal('bar')

    @mock.patch.object(session_local_storage, '_patch')
    def test_getattribute(self, mock_patch):
        self.assertEqual('bar', self.fl.foo)
        mock_patch.assert_called_with(self.fl)

    @mock.patch.object(session_local_storage, '_patch')
    def test_setattribute(self, mock_patch):
        self.fl.foo = 'baz'
        mock_patch.assert_called_with(self.fl)

    @mock.patch.object(session_local_storage, '_patch')
    def test_delattribute(self, mock_patch):
        del self.fl.foo
        mock_patch.assert_called_with(self.fl)


class TestSessionLocalDict(test_case.DslTestCase):
    def setUp(self):
        super(TestSessionLocalDict, self).setUp()
        self.sld = session_local_storage.SessionLocalDict(foo='bar')

    @mock.patch.object(helpers, 'get_execution_session', return_value=None)
    def test_data_no_session(self, mock_ges):
        self.assertEqual({'foo': 'bar'}, self.sld.data)
        self.sld.data = {'foo': 'baz'}

        mock_ges.assert_called_with()
        self.assertEqual({'foo': 'baz'}, self.sld.data)

    @mock.patch.object(helpers, 'get_execution_session',
                       return_value=mock.sentinel.session)
    def test_data(self, mock_ges):
        self.sld.data = mock.sentinel.data

        mock_ges.assert_called_with()
        self.assertEqual(mock.sentinel.data, self.sld.data)


class TestExecutionSessionMemoize(test_case.DslTestCase):
    @mock.patch.object(helpers, 'get_memoize_func',
                       return_value=mock.sentinel.mem_func)
    def test_execution_session_memoize(self, mock_gef):
        f = mock.MagicMock()
        f.return_value = 'im a function'
        new_f = session_local_storage.execution_session_memoize(f)
        self.assertEqual(f, mock_gef.call_args[0][0])
        self.assertIsInstance(mock_gef.call_args[0][1],
                              session_local_storage.SessionLocalDict)
        self.assertEqual(mock.sentinel.mem_func, new_f)
