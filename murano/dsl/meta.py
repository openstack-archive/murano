#    Copyright (c) 2016 Mirantis, Inc.
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

import abc
import operator
import weakref

import six

from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.dsl import object_store


class MetaProvider(object):
    @abc.abstractmethod
    def get_meta(self, context):
        raise NotImplementedError()


class MetaData(MetaProvider):
    def __init__(self, definition, target, scope_type):
        scope_type = weakref.ref(scope_type)
        definition = helpers.list_value(definition)
        factories = []
        used_types = set()
        for d in definition:
            if isinstance(d, dict):
                if len(d) != 1:
                    raise ValueError('Invalid Meta format')
                name = next(iter(d.keys()))
                props = d[name] or {}
            else:
                name = d
                props = {}
            type_obj = helpers.resolve_type(name, scope_type())
            if type_obj.usage != dsl_types.ClassUsages.Meta:
                raise ValueError('Only Meta classes can be attached')
            if target not in type_obj.targets:
                raise ValueError(
                    u'Meta class {} is not applicable here'.format(
                        type_obj.name))
            if type_obj in used_types and (
                    type_obj.cardinality != dsl_types.MetaCardinality.Many):
                raise ValueError('Cannot attach several Meta instances '
                                 'with cardinality One')

            used_types.add(type_obj)
            factory_maker = lambda template: \
                lambda context, store: helpers.instantiate(
                    template, owner=None, object_store=store,
                    context=context, scope_type=scope_type())

            factories.append(factory_maker({type_obj: props}))
        self._meta_factories = factories
        self._meta = None

    def get_meta(self, context):
        if self._meta is None:
            executor = helpers.get_executor(context)
            store = object_store.ObjectStore(executor)
            self._meta = list(map(
                lambda x: x(context, store),
                self._meta_factories))
        return self._meta


def merge_providers(initial_class, producer, context):
    def merger(cls_list, skip_list):
        result = set()
        all_meta = []
        for cls in cls_list:
            cls_skip_list = skip_list.copy()
            provider = producer(cls)
            meta = [] if provider is None else provider.get_meta(context)
            for item in meta:
                cardinality = item.type.cardinality
                inherited = item.type.inherited
                if cls is not initial_class and (
                        not inherited or item.type in skip_list):
                    continue
                if cardinality == dsl_types.MetaCardinality.One:
                    cls_skip_list.add(item.type)
                all_meta.append((cls, item))
            all_meta.extend(merger(cls.parents(initial_class), cls_skip_list))
        meta_types = {}
        for cls, item in all_meta:
            entry = meta_types.get(item.type)
            if entry is not None:
                if entry is not cls:
                    raise ValueError(
                        u'Found more than one instance of Meta {} '
                        u'with Cardinality One'.format(item.type.name))
                else:
                    continue

            if item.type.cardinality == dsl_types.MetaCardinality.One:
                meta_types[item.type] = cls
            result.add((cls, item))
        return result

    meta = merger([initial_class], set())
    return list(six.moves.map(operator.itemgetter(1), meta))
