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

import collections
import gc
import weakref

from oslo_log import log as logging

from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.dsl import murano_object


LOG = logging.getLogger(__name__)


class ObjectStore(object):
    def __init__(self, executor, parent_store=None, weak_store=True):
        self._parent_store = parent_store
        self._store = weakref.WeakValueDictionary() if weak_store else {}
        self._designer_attributes_store = {}
        self._executor = weakref.ref(executor)
        self._pending_destruction = set()

    @property
    def executor(self):
        return self._executor()

    def get(self, object_id, check_parent_store=True):
        result = self._store.get(object_id)
        if not result and self._parent_store and check_parent_store:
            return self._parent_store.get(object_id, check_parent_store)
        return result

    def has(self, object_id, check_parent_store=True):
        if object_id in self._store:
            return True
        if check_parent_store and self._parent_store:
            return self._parent_store.has(object_id, check_parent_store)
        return False

    def put(self, murano_object, object_id=None):
        self._store[object_id or murano_object.object_id] = murano_object

    def schedule_object_destruction(self, murano_object):
        self._pending_destruction.add(murano_object)
        self._store[murano_object.object_id] = murano_object

    def iterate(self):
        return self._store.keys()

    def remove(self, object_id):
        self._store.pop(object_id)

    def load(self, value, owner, default_type=None,
             scope_type=None, context=None, keep_ids=False,
             bypass_store=False):
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
                    if not bypass_store:
                        self.put(obj)
            return result

    @staticmethod
    def _get_designer_attributes(header):
        return dict((k, v) for k, v in header.items()
                    if str(k).startswith('_'))

    def designer_attributes(self, object_id):
        return self._designer_attributes_store.get(object_id, {})

    @property
    def initializing(self):
        return False

    @property
    def parent_store(self):
        return self._parent_store

    def cleanup(self):
        LOG.debug('Cleaning up orphan objects')
        with helpers.with_object_store(self):
            n = self._collect_garbage()
            LOG.debug('{} orphan objects were destroyed'.format(n))
            return n

    def prepare_finalize(self, used_objects):
        used_objects = set(used_objects) if used_objects else []
        sentenced_objects = [
            obj for obj in self._store.values()
            if obj not in used_objects
        ]
        with helpers.with_object_store(self):
            if sentenced_objects:
                self._pending_destruction.update(sentenced_objects)
                for __ in self._destroy_garbage(sentenced_objects):
                    pass

    def finalize(self):
        with helpers.with_object_store(self):
            for t in self._store.values():
                t.mark_destroyed(True)
        self._pending_destruction.clear()
        self._store.clear()

    def _collect_garbage(self):
        repeat = True
        count = 0
        while repeat:
            repeat = False
            gc.collect()
            for obj in gc.garbage:
                if (isinstance(obj, murano_object.RecyclableMuranoObject) and
                        obj.executor is self._executor()):
                    repeat = True
                    if obj.initialized and not obj.destroyed:
                        self.schedule_object_destruction(obj)
                    else:
                        obj.mark_destroyed(True)
            obj = None
            del gc.garbage[:]
            if self._pending_destruction:
                for obj in self._destroy_garbage(self._pending_destruction):
                    if obj in self._pending_destruction:
                        repeat = True
                        obj.mark_destroyed()
                        self._pending_destruction.remove(obj)
                        count += 1
        return count

    def is_doomed(self, obj):
        return obj.destroyed or obj in self._pending_destruction

    def _destroy_garbage(self, sentenced_objects):
        dd_graph = {}

        # NOTE(starodubcevna): construct a graph which looks like:
        # {
        #   obj1: [subscriber1, subscriber2],
        #   obj2: [subscriber2, subscriber3]
        # }
        for obj in sentenced_objects:
            obj_subscribers = [obj.owner]

            for dd in obj.destruction_dependencies:
                subscriber = dd['subscriber']
                if subscriber:
                    subscriber = subscriber()
                if subscriber and subscriber not in obj_subscribers:
                    obj_subscribers.append(subscriber)

            dd_graph[obj] = obj_subscribers

        def topological(graph):
            """Topological sort implementation

            This implementation will work even if we have cycle dependencies,
            e.g. [a->b, b->c, c->a]. In this case the order of deletion will be
            undefined and it's okay.
            """

            visited = collections.defaultdict(int)
            indexes = collections.defaultdict(int)

            def dfs(obj):
                visited[obj] += 1
                subscribers = graph.get(obj)
                if subscribers is not None:
                    m = 0
                    for i, subscriber in enumerate(subscribers):
                        if i == 0 or not visited[subscriber]:
                            for t in dfs(subscriber):
                                yield t
                        m = max(m, indexes[subscriber])

                    if visited.get(obj, 0) <= 2:
                        visited[obj] += 1
                        indexes[obj] = m + 1
                        yield obj, m + 1

            for i, obj in enumerate(graph.keys()):
                if not visited[obj]:
                    for t in dfs(obj):
                        yield t

            visited.clear()
            indexes.clear()

        order = collections.defaultdict(list)
        for obj, index in topological(dd_graph):
            order[index].append(obj)

        for key in sorted(order):
            group = order[key]
            self.executor.signal_destruction_dependencies(*group)

        for key in sorted(order, reverse=True):
            group = order[key]
            self.executor.destroy_objects(*group)
            for t in group:
                yield t


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
            parent_store.executor, parent_store, weak_store=False)
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
        is_tmp_object = (object_id is None and
                         owner is not self._root_owner and
                         self._initializing)
        obj = None if object_id is None else self.get(
            object_id, self._keep_ids)
        if not obj:
            if is_tmp_object or helpers.is_objects_dry_run_mode():
                mo_type = murano_object.MuranoObject
            else:
                mo_type = murano_object.RecyclableMuranoObject
            obj = mo_type(
                class_obj, owner,
                name=parsed['name'],
                metadata=parsed['metadata'],
                object_id=object_id if self._keep_ids else None)
            obj.load_dependencies(parsed['dependencies'])
            if parsed['destroyed']:
                obj.mark_destroyed()
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
