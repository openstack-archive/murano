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

import weakref

import six

from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.dsl import murano_object


class ObjectStore(object):
    def __init__(self, executor, parent_store=None):
        self._parent_store = parent_store
        self._store = {}
        self._designer_attributes_store = {}
        self._executor = weakref.ref(executor)

    @property
    def executor(self):
        return self._executor()

    def get(self, object_id):
        result = self._store.get(object_id)
        if not result and self._parent_store:
            return self._parent_store.get(object_id)
        return result

    def has(self, object_id, check_parent_store=True):
        if object_id in self._store:
            return True
        if check_parent_store and self._parent_store:
            return self._parent_store.has(object_id, check_parent_store)
        return False

    def put(self, murano_object, object_id=None):
        self._store[object_id or murano_object.object_id] = murano_object

    def iterate(self):
        return six.iterkeys(self._store)

    def remove(self, object_id):
        self._store.pop(object_id)

    def load(self, value, owner, default_type=None,
             scope_type=None, context=None, keep_ids=False):
        # do the object model load in a temporary object store and copy
        # loaded objects here after that
        model_store = InitializationObjectStore(
            owner, self, keep_ids)
        with helpers.with_object_store(model_store):
            result = model_store.load(
                value, owner, scope_type=scope_type,
                default_type=default_type, context=context)
            for obj_id in model_store.iterate():
                obj = model_store.get(obj_id)
                if obj.initialized:
                    self.put(obj)
            return result

    @staticmethod
    def _get_designer_attributes(header):
        return dict((k, v) for k, v in six.iteritems(header)
                    if str(k).startswith('_'))

    def designer_attributes(self, object_id):
        return self._designer_attributes_store.get(object_id, {})

    @property
    def initializing(self):
        return False

    @property
    def parent_store(self):
        return self._parent_store


# Temporary ObjectStore to load object graphs. Does 2-phase load
# and maintains internal state on what phase is currently running
# as well as objects that are in the middle of initialization.
# Required in order to isolate semi-initialized objects from regular
# objects in main ObjectStore and internal state between graph loads
# in different threads. Once the load is done all objects are copied
# to the parent ObjectStore
class InitializationObjectStore(ObjectStore):
    def __init__(self, root_owner, parent_store, keep_ids):
        super(InitializationObjectStore, self).__init__(
            parent_store.executor, parent_store)
        self._initializing = False
        self._root_owner = root_owner
        self._keep_ids = keep_ids
        self._initializers = []

    @property
    def initializing(self):
        return self._initializing

    def load(self, value, owner, default_type=None,
             scope_type=None, context=None, **kwargs):
        parsed = helpers.parse_object_definition(value, scope_type, context)
        if not parsed:
            raise ValueError('Invalid object representation format')

        if owner is self._root_owner:
            self._initializing = True

        class_obj = parsed['type'] or default_type
        if not class_obj:
            raise ValueError(
                'Invalid object representation: '
                'no type information was provided')
        if isinstance(class_obj, dsl_types.MuranoTypeReference):
            class_obj = class_obj.type
        object_id = parsed['id']
        obj = None if object_id is None else self.get(object_id)
        if not obj:
            obj = murano_object.MuranoObject(
                class_obj, helpers.weak_proxy(owner),
                name=parsed['name'],
                object_id=object_id if self._keep_ids else None)
            self.put(obj, object_id or obj.object_id)

            system_value = ObjectStore._get_designer_attributes(
                parsed['extra'])
            self._designer_attributes_store[object_id] = system_value

        if context is None:
            context = self.executor.create_object_context(obj)

        def run_initialize():
            self._initializers.extend(
                obj.initialize(context, parsed['properties']))

        run_initialize()
        if owner is self._root_owner:
            self._initializing = False
            run_initialize()

        if owner is self._root_owner:
            with helpers.with_object_store(self.parent_store):
                for fn in self._initializers:
                    fn()

        return obj
