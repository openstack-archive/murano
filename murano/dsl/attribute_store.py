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

import murano.dsl.murano_object as murano_object


class AttributeStore(object):
    def __init__(self):
        self._attributes = {}

    def set(self, tagged_object, owner_type, name, value):
        if isinstance(value, murano_object.MuranoObject):
            value = value.object_id

        key = (tagged_object.object_id, owner_type.name, name)
        if value is None:
            self._attributes.pop(key, None)
        else:
            self._attributes[key] = value

    def get(self, tagged_object, owner_type, name):
        return self._attributes.get(
            (tagged_object.object_id, owner_type.name, name))

    def serialize(self, known_objects):
        return [
            [key[0], key[1], key[2], value]
            for key, value
            in self._attributes.iteritems()
            if key[0] in known_objects
        ]

    def load(self, data):
        for item in data:
            if item[3] is not None:
                self._attributes[(item[0], item[1], item[2])] = item[3]
