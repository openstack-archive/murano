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

from murano.dsl import helpers


class Object(object):
    def __init__(self, __name, **kwargs):
        self.data = {
            '?': {
                'type': __name,
                'id': helpers.generate_id()
            }
        }
        self.data.update(kwargs)

    @property
    def id(self):
        return self.data['?']['id']

    @property
    def type_name(self):
        return self.data['?']['type']


class Attribute(object):
    def __init__(self, obj, key, value):
        self._value = value
        self._key = key
        self._obj = obj

    @property
    def obj(self):
        return self._obj

    @property
    def key(self):
        return self._key

    @property
    def value(self):
        return self._value


class Ref(object):
    def __init__(self, obj):
        self._id = obj.id

    @property
    def id(self):
        return self._id


def build_model(root):
    if isinstance(root, dict):
        for key, value in root.items():
            root[key] = build_model(value)
    elif isinstance(root, list):
        for i in range(len(root)):
            root[i] = build_model(root[i])
    elif isinstance(root, Object):
        return build_model(root.data)
    elif isinstance(root, Ref):
        return root.id
    elif isinstance(root, Attribute):
        return [root.obj.id, root.obj.type_name, root.key, root.value]
    return root
