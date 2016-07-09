# Copyright (c) 2016 Mirantis, Inc.
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

import mock
import semantic_version

from murano.tests.unit.dsl.foundation import object_model as om
from murano.tests.unit.dsl.foundation import test_case


class TestVersioning(test_case.DslTestCase):
    def test_provided_version(self):
        version = '1.11.111'
        sem_version = semantic_version.Spec('==' + version)
        model = om.Object('Empty', class_version=version)
        m = mock.MagicMock(return_value=self._package_loader._package)
        self._package_loader.load_class_package = m
        self.new_runner(model)
        m.assert_called_once_with('Empty', sem_version)

    def test_empty_provided_version(self):
        version = ''
        sem_version = semantic_version.Spec('>=0.0.0', '<1.0.0-0')
        model = om.Object('Empty', class_version=version)
        m = mock.MagicMock(return_value=self._package_loader._package)
        self._package_loader.load_class_package = m
        self.new_runner(model)
        m.assert_called_once_with('Empty', sem_version)

    def test_several_in_row(self):
        version = '>3.0.0,<=4.1'
        sem_version = semantic_version.Spec('>3.0.0', '<4.2.0-0')
        model = om.Object('Empty', class_version=version)
        m = mock.MagicMock(return_value=self._package_loader._package)
        self._package_loader.load_class_package = m
        self.new_runner(model)
        m.assert_called_once_with('Empty', sem_version)
