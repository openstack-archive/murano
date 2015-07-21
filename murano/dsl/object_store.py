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

from murano.dsl import constants
from murano.dsl import dsl_types
from murano.dsl import helpers


class ObjectStore(object):
    def __init__(self, context, parent_store=None):
        self._context = context.create_child_context()
        self._class_loader = helpers.get_class_loader(context)
        self._context[constants.CTX_OBJECT_STORE] = self
        self._parent_store = parent_store
        self._store = {}
        self._designer_attributes_store = {}
        self._initializing = False

    @property
    def initializing(self):
        return self._initializing

    @property
    def class_loader(self):
        return self._class_loader

    @property
    def context(self):
        return self._context

    def get(self, object_id):
        if object_id in self._store:
            result = self._store[object_id]
            if not isinstance(result, dsl_types.MuranoObject):
                result = None
            return result
        if self._parent_store:
            return self._parent_store.get(object_id)
        return None

    def has(self, object_id):
        return object_id in self._store

    def put(self, murano_object):
        self._store[murano_object.object_id] = murano_object

    def load(self, value, owner, defaults=None):
        if value is None:
            return None
        if '?' not in value or 'type' not in value['?']:
            raise ValueError()
        system_key = value['?']
        object_id = system_key['id']
        obj_type = system_key['type']
        class_obj = self._class_loader.get_class(obj_type)
        if not class_obj:
            raise ValueError()

        try:
            if owner is None:
                self._initializing = True

            if object_id in self._store:
                factory = self._store[object_id]
                if isinstance(factory, dsl_types.MuranoObject):
                    return factory
            else:
                factory = class_obj.new(
                    owner, self, context=self.context,
                    name=system_key.get('name'),
                    object_id=object_id, defaults=defaults)
                self._store[object_id] = factory
                system_value = ObjectStore._get_designer_attributes(system_key)
                self._designer_attributes_store[object_id] = system_value

            obj = factory(**value)
            if not self._initializing:
                self._store[object_id] = obj
            if owner is None:
                self._initializing = False
                self._store[object_id] = factory(**value)
        finally:
            if owner is None:
                self._initializing = False

        return factory.object

    @staticmethod
    def _get_designer_attributes(header):
        return dict((k, v) for k, v in header.iteritems()
                    if str(k).startswith('_'))

    def designer_attributes(self, object_id):
        return self._designer_attributes_store.get(object_id, {})
