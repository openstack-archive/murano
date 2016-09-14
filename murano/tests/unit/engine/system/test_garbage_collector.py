#    Copyright (c) 2016 Mirantis, Inc.
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

import _weakref

import mock
from testtools import matchers
import unittest

from murano.dsl import dsl
from murano.dsl import exceptions
from murano.dsl import murano_method
from murano.dsl import murano_object
from murano.dsl import murano_type
from murano.engine.system import garbage_collector
from murano.tests.unit import base


class TestGarbageCollector(base.MuranoTestCase):
    def setUp(self):
        super(TestGarbageCollector, self).setUp()

        self.mock_subscriber = mock.MagicMock(spec=murano_object.MuranoObject)
        self.mock_class = mock.MagicMock(spec=murano_type.MuranoClass)
        self.mock_method = mock.MagicMock(spec=murano_method.MuranoMethod)
        self.mock_method.name = "mockHandler"
        self.mock_class.methods = mock.PropertyMock(
            return_value={"mockHandler": self.mock_method})
        self.mock_subscriber.type = self.mock_class
        self.mock_subscriber.object_id = "1234"

    @mock.patch("murano.dsl.helpers.get_caller_context")
    @mock.patch("murano.dsl.helpers.get_this")
    def test_set_dd(self, this, caller_context):
        this.return_value = self.mock_subscriber
        target_0 = mock.MagicMock(spec=dsl.MuranoObjectInterface)
        target_0.object = self.mock_subscriber
        target_0.object.real_this = self.mock_subscriber
        target_0.object.dependencies = {}
        garbage_collector.GarbageCollector.subscribe_destruction(
            target_0, handler="mockHandler")
        dep = self.mock_subscriber.dependencies["onDestruction"]
        self.assertThat(dep, matchers.HasLength(1))
        dep = dep[0]
        self.assertEqual("mockHandler", dep["handler"])
        self.assertEqual(self.mock_subscriber, dep["subscriber"]())

    @mock.patch("murano.dsl.helpers.get_caller_context")
    @mock.patch("murano.dsl.helpers.get_this")
    def test_unset_dd(self, this, caller_context):
        this.return_value = self.mock_subscriber
        target_1 = mock.MagicMock(spec=dsl.MuranoObjectInterface)
        target_1.object = self.mock_subscriber
        target_1.object.real_this = self.mock_subscriber
        target_1.object.dependencies = (
            {"onDestruction": [{
                "subscriber": _weakref.ref(self.mock_subscriber),
                "handler": "mockHandler"
            }]})
        garbage_collector.GarbageCollector.unsubscribe_destruction(
            target_1, handler="mockHandler")
        self.assertEqual(
            [], self.mock_subscriber.dependencies["onDestruction"])

    @unittest.skip("WIP")
    @mock.patch("murano.dsl.helpers.get_caller_context")
    @mock.patch("murano.dsl.helpers.get_this")
    def test_set_wrong_handler(self, this, caller_context):
        this.return_value = self.mock_subscriber
        target_2 = mock.MagicMock(spec=dsl.MuranoObjectInterface)
        target_2.object = mock.MagicMock(murano_object.MuranoObject)
        target_2.object.dependencies = {}
        self.assertRaises(
            exceptions.NoMethodFound,
            garbage_collector.GarbageCollector.subscribe_destruction,
            target_2, handler="wrongHandler")
