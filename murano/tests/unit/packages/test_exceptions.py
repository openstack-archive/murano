# Copyright (c) 2016 AT&T Corp
# All Rights Reserved.
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

import six

from murano.packages import exceptions
import murano.tests.unit.base as test_base


class TestExceptions(test_base.MuranoTestCase):

    def test_package_class_load_error(self):
        class_name = 'test class name'
        message = 'test message'
        error = exceptions.PackageClassLoadError(class_name=class_name,
                                                 message=message)
        expected = 'Unable to load class "{0}" from package: {1}'\
                   .format(class_name, message)
        if six.PY2:
            self.assertEqual(expected, error.message)
        elif six.PY34:
            self.assertEqual(expected, error.args[0])

    def test_package_ui_load_error(self):
        messages = ['', 'test_message']
        for message in messages:
            error = exceptions.PackageUILoadError(message=message)
            expected = 'Unable to load ui definition from package'
            if message:
                expected += ': {0}'.format(message)
            if six.PY2:
                self.assertEqual(expected, error.message)
            elif six.PY34:
                self.assertEqual(expected, error.args[0])

    def test_package_format_error(self):
        messages = ['', 'test_message']
        for message in messages:
            error = exceptions.PackageFormatError(message=message)
            expected = 'Incorrect package format'
            if message:
                expected += ': {0}'.format(message)
            if six.PY2:
                self.assertEqual(expected, error.message)
            elif six.PY34:
                self.assertEqual(expected, error.args[0])
