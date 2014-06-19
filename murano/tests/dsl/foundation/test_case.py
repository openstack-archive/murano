# Copyright (c) 2014 Mirantis, Inc.
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


import inspect
import os.path

import eventlet.debug

from murano.tests import base
from murano.tests.dsl.foundation import runner
from murano.tests.dsl.foundation import test_class_loader


class DslTestCase(base.MuranoTestCase):
    def setUp(self):
        super(DslTestCase, self).setUp()
        directory = os.path.join(os.path.dirname(
            inspect.getfile(self.__class__)), 'meta')
        sys_class_loader = test_class_loader.TestClassLoader(
            os.path.join(directory, '../../../../meta/io.murano/Classes'),
            'murano.io')
        self._class_loader = test_class_loader.TestClassLoader(
            directory, 'tests', sys_class_loader)
        self.register_function(
            lambda data: self._traces.append(data()), 'trace')
        self._traces = []

    def new_runner(self, model):
        return runner.Runner(model, self.class_loader)

    @property
    def traces(self):
        return self._traces

    @property
    def class_loader(self):
        return self._class_loader

    def register_function(self, func, name):
        self.class_loader.register_function(func, name)

    @classmethod
    def setUpClass(cls):
        eventlet.debug.hub_exceptions(False)
