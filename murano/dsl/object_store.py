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

import inspect

import murano.dsl.helpers as helpers


class ObjectStore(object):
    def __init__(self, class_loader, parent_store=None):
        self._class_loader = class_loader
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

    def get(self, object_id):
        if object_id in self._store:
            return self._store[object_id]
        if self._parent_store:
            return self._parent_store.get(object_id)
        return None

    def has(self, object_id):
        return object_id in self._store

    def put(self, murano_object):
        self._store[murano_object.object_id] = murano_object

    def load(self, value, owner, context, defaults=None):
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
        if object_id in self._store:
            obj = self._store[object_id]
        else:
            obj = class_obj.new(owner, self, context=context,
                                object_id=object_id, defaults=defaults)
            self._store[object_id] = obj
            self._designer_attributes_store[object_id] = \
                ObjectStore._get_designer_attributes(system_key)

        argspec = inspect.getargspec(obj.initialize).args
        if '_context' in argspec:
            value['_context'] = context
        if '_parent' in argspec:
            value['_owner'] = owner

        try:
            if owner is None:
                self._initializing = True
            obj.initialize(**value)
            if owner is None:
                self._initializing = False
                obj.initialize(**value)
        finally:
            if owner is None:
                self._initializing = False

        if not self.initializing:
            executor = helpers.get_executor(context)
            methods = obj.type.find_all_methods('initialize')
            methods.reverse()
            for method in methods:
                method.invoke(executor, obj, {})
        return obj

    @staticmethod
    def _get_designer_attributes(header):
        return dict((k, v) for k, v in header.iteritems()
                    if str(k).startswith('_'))

    def designer_attributes(self, object_id):
        return self._designer_attributes_store.get(object_id, {})
