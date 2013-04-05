# Copyright (c) 2013 Mirantis Inc.
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


class Context(object):
    def __init__(self, parent=None):
        self._parent = parent
        self._data = None

    def _get_data(self):
        if self._data is None:
            self._data = {} if self._parent is None \
                else self._parent._get_data().copy()
        return self._data

    def __getitem__(self, item):
        context, path = self._parseContext(item)
        return context._get_data().get(path)

    def __setitem__(self, key, value):
        context, path = self._parseContext(key)
        context._get_data()[path] = value

    def _parseContext(self, path):
        context = self
        index = 0
        for c in path:
            if c == ':' and context._parent is not None:
                context = context._parent
            elif c == '/':
                while context._parent is not None:
                    context = context._parent
            else:
                break

            index += 1

        return context, path[index:]

    def assign_from(self, context, copy=False):
        self._parent = context._parent
        self._data = context._data
        if copy and self._data is not None:
            self._data = self._data.copy()

    @property
    def parent(self):
        return self._parent

    def __str__(self):
        if self._data is not None:
            return str(self._data)
        if self._parent:
            return str(self._parent)
        return str({})
