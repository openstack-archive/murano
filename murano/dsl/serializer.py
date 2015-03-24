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
import types

import murano.dsl.helpers as helpers
import murano.dsl.murano_method as murano_method
import murano.dsl.murano_object as murano_object


class ObjRef(object):
    def __init__(self, obj):
        self.ref_obj = obj


def serialize_object(obj):
    if isinstance(obj, (collections.Sequence, collections.Set)) and not \
            isinstance(obj, types.StringTypes):
        return [serialize_object(t) for t in obj]
    elif isinstance(obj, collections.Mapping):
        result = {}
        for key, value in obj.iteritems():
            result[key] = serialize_object(value)
        return result
    elif isinstance(obj, murano_object.MuranoObject):
        return _serialize_object(obj, None)[0]
    return obj


def _serialize_object(root_object, designer_attributes=None):
    serialized_objects = set()
    tree = _pass1_serialize(
        root_object, None, serialized_objects, designer_attributes)
    _pass2_serialize(tree, serialized_objects)
    return tree, serialized_objects


def serialize_model(root_object, executor):
    if root_object is None:
        tree = None
        tree_copy = None
        attributes = []
    else:
        tree, serialized_objects = _serialize_object(
            root_object, executor.object_store.designer_attributes)
        tree_copy, _ = _serialize_object(root_object, None)
        attributes = executor.attribute_store.serialize(serialized_objects)

    return {
        'Objects': tree,
        'ObjectsCopy': tree_copy,
        'Attributes': attributes
    }


def _cmp_objects(obj1, obj2):
    if obj1 is None and obj2 is None:
        return True
    if obj1 is None or obj2 is None:
        return False
    return obj1.object_id == obj2.object_id


def _serialize_available_action(obj):
    def _serialize(obj_type):
        actions = {}
        for name, method in obj_type.methods.iteritems():
            if method.usage == murano_method.MethodUsages.Action:
                action_id = '{0}_{1}'.format(obj.object_id, name)
                actions[action_id] = {
                    'name': name,
                    'enabled': True
                }
        for parent in obj_type.parents:
            parent_actions = _serialize(parent)
            actions = helpers.merge_dicts(parent_actions, actions)
        return actions
    return _serialize(obj.type)


def _merge_actions(dict1, dict2):
    result = helpers.merge_dicts(dict1, dict2)
    for action_id in dict1:
        if action_id not in dict2:
            del result[action_id]
    return result


def _pass1_serialize(value, parent, serialized_objects,
                     designer_attributes_getter):
    if isinstance(value, (types.StringTypes, types.IntType, types.FloatType,
                          types.BooleanType, types.NoneType)):
        return value
    elif isinstance(value, murano_object.MuranoObject):
        if not _cmp_objects(value.owner, parent) \
                or value.object_id in serialized_objects:
            return ObjRef(value)
        else:
            result = value.to_dictionary()
            if designer_attributes_getter is not None:
                result['?'].update(designer_attributes_getter(value.object_id))
                # deserialize and merge list of actions
                actions = _serialize_available_action(value)
                result['?']['_actions'] = _merge_actions(
                    result['?'].get('_actions', {}), actions)
            serialized_objects.add(value.object_id)
            return _pass1_serialize(
                result, value, serialized_objects, designer_attributes_getter)

    elif isinstance(value, types.DictionaryType):
        result = {}
        for d_key, d_value in value.iteritems():
            result_key = str(d_key)
            result[result_key] = _pass1_serialize(
                d_value, parent, serialized_objects,
                designer_attributes_getter)
        return result
    elif isinstance(value, types.ListType):
        return [_pass1_serialize(t, parent, serialized_objects,
                                 designer_attributes_getter) for t in value]
    elif isinstance(value, types.TupleType):
        return _pass1_serialize(
            list(value), parent, serialized_objects,
            designer_attributes_getter)
    else:
        raise ValueError()


def _pass2_serialize(value, serialized_objects):
    if isinstance(value, types.DictionaryType):
        for d_key, d_value in value.iteritems():
            if isinstance(d_value, ObjRef):
                if d_value.ref_obj.object_id in serialized_objects:
                    value[d_key] = d_value.ref_obj.object_id
                else:
                    value[d_key] = None
            else:
                _pass2_serialize(d_value, serialized_objects)
    elif isinstance(value, types.ListType):
        index = 0
        while index < len(value):
            item = value[index]
            if isinstance(item, ObjRef):
                if item.ref_obj.object_id in serialized_objects:
                    value[index] = item.ref_obj.object_id
                else:
                    value.pop(index)
                    index -= 1
            else:
                _pass2_serialize(item, serialized_objects)
            index += 1
