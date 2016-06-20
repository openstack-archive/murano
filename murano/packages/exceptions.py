# Copyright (c) 2014 Mirantis Inc.
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

import six

import murano.common.exceptions as e


class PackageException(e.Error):
    if six.PY2:
        def __str__(self):
            return six.text_type(self.message).encode('UTF-8')


class PackageClassLoadError(PackageException):
    def __init__(self, class_name, message=None):
        msg = 'Unable to load class "{0}" from package'.format(class_name)
        if message:
            msg += ": " + message
        super(PackageClassLoadError, self).__init__(msg)


class PackageUILoadError(PackageException):
    def __init__(self, message=None):
        msg = 'Unable to load ui definition from package'
        if message:
            msg += ": " + message
        super(PackageUILoadError, self).__init__(msg)


class PackageLoadError(PackageException):
    pass


class PackageFormatError(PackageLoadError):
    def __init__(self, message=None):
        msg = 'Incorrect package format'
        if message:
            msg += ': ' + message
        super(PackageFormatError, self).__init__(msg)
