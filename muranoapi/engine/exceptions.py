#    Copyright (c) 2014 Mirantis, Inc.
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


class ReturnException(Exception):
    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value


class BreakException(Exception):
    pass


class NoMethodFound(Exception):
    def __init__(self, name):
        super(NoMethodFound, self).__init__('Method %s is not found' % name)


class NoClassFound(Exception):
    def __init__(self, name):
        super(NoClassFound, self).__init__('Class %s is not found' % name)


class AmbiguousMethodName(Exception):
    def __init__(self, name):
        super(AmbiguousMethodName, self).__init__(
            'Found more that one method %s' % name)


class NoWriteAccess(Exception):
    def __init__(self, name):
        super(NoWriteAccess, self).__init__(
            'Property %s is immutable to the caller' % name)
