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

import weakref

import mock
from testtools import matchers

from murano.dsl import exceptions
from murano.dsl import murano_method
from murano.dsl import murano_object
from murano.dsl import murano_type
from murano.dsl.principal_objects import garbage_collector
from murano.tests.unit import base


class TestGarbageCollector(base.MuranoTestCase):
    def setUp(self):
        super(TestGarbageCollector, self).setUp()

        self.subscriber = mock.MagicMock(spec=murano_object.MuranoObject)
        self.subscriber.real_this = self.subscriber

        mock_class = mock.MagicMock(spec=murano_type.MuranoClass)
        mock_method = mock.MagicMock(spec=murano_method.MuranoMethod)
        mock_method.name = "mockHandler"
        mock_class.methods = mock.PropertyMock(
            return_value={"mockHandler": mock_method})

        def find_single_method(name):
            if name != 'mockHandler':
                raise exceptions.NoMethodFound(name)

        mock_class.find_single_method = find_single_method
        self.subscriber.type = mock_class

        self.publisher = mock.MagicMock(spec=murano_object.MuranoObject)
        self.publisher.real_this = self.publisher

    def test_set_dd(self):
        self.publisher.destruction_dependencies = []
        garbage_collector.GarbageCollector.subscribe_destruction(
            self.publisher, self.subscriber, handler="mockHandler")
        dep = self.publisher.destruction_dependencies
        self.assertThat(dep, matchers.HasLength(1))
        dep = dep[0]
        self.assertEqual("mockHandler", dep["handler"])
        self.assertEqual(self.subscriber, dep["subscriber"]())

    def test_unset_dd(self):
        self.publisher.destruction_dependencies = [{
            "subscriber": weakref.ref(self.subscriber),
            "handler": "mockHandler"
        }]
        garbage_collector.GarbageCollector.unsubscribe_destruction(
            self.publisher, self.subscriber, handler="mockHandler")
        self.assertEqual(
            [], self.publisher.destruction_dependencies)

    def test_set_wrong_handler(self):
        self.assertRaises(
            exceptions.NoMethodFound,
            garbage_collector.GarbageCollector.subscribe_destruction,
            self.publisher, self.subscriber, handler="invalidHandler")
        self.assertRaises(
            exceptions.NoMethodFound,
            garbage_collector.GarbageCollector.unsubscribe_destruction,
            self.publisher, self.subscriber, handler="invalidHandler")
