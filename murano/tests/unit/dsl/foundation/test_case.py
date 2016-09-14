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

from murano.tests.unit import base
from murano.tests.unit.dsl.foundation import runner
from murano.tests.unit.dsl.foundation import test_package_loader


class DslTestCase(base.MuranoTestCase):
    def setUp(self):
        super(DslTestCase, self).setUp()
        directory = os.path.join(os.path.dirname(
            inspect.getfile(self.__class__)), 'meta')
        root_meta_directory = os.path.join(
            os.path.dirname(__file__), '../../../../../meta')
        sys_package_loader = test_package_loader.TestPackageLoader(
            os.path.join(root_meta_directory, 'io.murano/Classes'),
            'io.murano')
        self._package_loader = test_package_loader.TestPackageLoader(
            directory, 'tests', sys_package_loader)
        self._functions = {}
        self.register_function(
            lambda data: self._traces.append(data), 'trace')
        self._traces = []
        self._runners = []
        eventlet.debug.hub_exceptions(False)

    def new_runner(self, model):
        r = runner.Runner(model, self.package_loader, self._functions)
        self._runners.append(r)
        return r

    def tearDown(self):
        super(DslTestCase, self).tearDown()
        for r in self._runners:
            r.executor.finalize(r.root)

    @property
    def traces(self):
        return self._traces

    @traces.deleter
    def traces(self):
        self._traces = []

    @property
    def package_loader(self):
        return self._package_loader

    def register_function(self, func, name):
        self._functions[name] = func

    @staticmethod
    def find_attribute(model, obj_id, obj_type, name):
        for entry in model['Attributes']:
            if tuple(entry[:3]) == (obj_id, obj_type, name):
                return entry[3]
