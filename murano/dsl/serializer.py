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


import six
from yaql import utils

from murano.dsl import dsl
from murano.dsl import dsl_types


class ObjRef(object):
    def __init__(self, obj):
        self.ref_obj = obj


def serialize(obj):
    return serialize_model(obj, None, True)[0]['Objects']


def _serialize_object(root_object, designer_attributes, allow_refs):
    serialized_objects = set()

    obj = root_object
    while True:
        obj, need_another_pass = _pass12_serialize(
            obj, None, serialized_objects, designer_attributes)
        if not need_another_pass:
            break
    tree = [obj]
    _pass3_serialize(tree, serialized_objects, allow_refs)
    return tree[0], serialized_objects


def serialize_model(root_object, executor, allow_refs=False):
    if executor is not None:
        designer_attributes = executor.object_store.designer_attributes
    else:
        designer_attributes = None

    if root_object is None:
        tree = None
        tree_copy = None
        attributes = []
        serialized_objects = set()
    else:
        tree, serialized_objects = _serialize_object(
            root_object, designer_attributes, allow_refs)
        tree_copy, _ = _serialize_object(root_object, None, allow_refs)
        if executor is not None:
            attributes = executor.attribute_store.serialize(serialized_objects)
        else:
            attributes = []

    return {
        'Objects': tree,
        'ObjectsCopy': tree_copy,
        'Attributes': attributes
    }, serialized_objects


def _serialize_available_action(obj, current_actions):
    result = {}
    actions = obj.type.find_methods(
        lambda m: m.usage == dsl_types.MethodUsages.Action)
    for action in actions:
        action_id = '{0}_{1}'.format(obj.object_id, action.name)
        entry = current_actions.get(action_id, {'enabled': True})
        entry['name'] = action.name
        result[action_id] = entry
    return result


def _pass12_serialize(value, parent, serialized_objects,
                      designer_attributes_getter):
    if isinstance(value, dsl.MuranoObjectInterface):
        value = value.object
    if isinstance(value, (six.string_types,
                          int, float, bool)) or value is None:
        return value, False
    if isinstance(value, dsl_types.MuranoObject):
        if value.owner is not parent or value.object_id in serialized_objects:
            return ObjRef(value), True
    elif isinstance(value, ObjRef):
        if (value.ref_obj.object_id not in serialized_objects and
                is_nested_in(value.ref_obj.owner, parent)):
            value = value.ref_obj
        else:
            return value, False
    if isinstance(value, dsl_types.MuranoObject):
        result = value.to_dictionary()
        if designer_attributes_getter is not None:
            result['?'].update(designer_attributes_getter(value.object_id))
            # deserialize and merge list of actions
            result['?']['_actions'] = _serialize_available_action(
                value, result['?'].get('_actions', {}))
        serialized_objects.add(value.object_id)
        return _pass12_serialize(
            result, value, serialized_objects, designer_attributes_getter)
    elif isinstance(value, utils.MappingType):
        result = {}
        need_another_pass = False

        for d_key, d_value in six.iteritems(value):
            result_key = str(d_key)
            result_value = _pass12_serialize(
                d_value, parent, serialized_objects,
                designer_attributes_getter)
            result[result_key] = result_value[0]
            if result_value[1]:
                need_another_pass = True
        return result, need_another_pass
    elif utils.is_sequence(value) or isinstance(value, utils.SetType):
        need_another_pass = False
        result = []
        for t in value:
            v, nmp = _pass12_serialize(
                t, parent, serialized_objects, designer_attributes_getter)
            if nmp:
                need_another_pass = True
            result.append(v)
        return result, need_another_pass
    else:
        raise ValueError()


def _pass3_serialize(value, serialized_objects, allow_refs=False):
    if isinstance(value, dict):
        for d_key, d_value in value.items():
            if isinstance(d_value, ObjRef):
                if (d_value.ref_obj.object_id in serialized_objects or
                        allow_refs):
                    value[d_key] = d_value.ref_obj.object_id
                else:
                    del value[d_key]
            else:
                _pass3_serialize(d_value, serialized_objects, allow_refs)
    elif isinstance(value, list):
        index = 0
        while index < len(value):
            item = value[index]
            if isinstance(item, ObjRef):
                if item.ref_obj.object_id in serialized_objects or allow_refs:
                    value[index] = item.ref_obj.object_id
                else:
                    value.pop(index)
                    index -= 1
            else:
                _pass3_serialize(item, serialized_objects, allow_refs)
            index += 1
    return value


def is_nested_in(obj, ancestor):
    while True:
        if obj is ancestor:
            return True
        if obj is None:
            return False
        obj = obj.owner
