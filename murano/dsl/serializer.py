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
from murano.dsl import helpers


class ObjRef(object):
    def __init__(self, obj):
        self.ref_obj = obj


def serialize(obj, executor,
              serialization_type=dsl_types.DumpTypes.Serializable,
              allow_refs=True):
    with helpers.with_object_store(executor.object_store):
        return serialize_model(
            obj, executor, allow_refs,
            make_copy=False,
            serialize_attributes=False,
            serialize_actions=False,
            serialization_type=serialization_type,
            with_destruction_dependencies=False)['Objects']


def _serialize_object(root_object, designer_attributes, allow_refs,
                      executor, serialize_actions=True,
                      serialization_type=dsl_types.DumpTypes.Serializable,
                      with_destruction_dependencies=True):
    serialized_objects = set()

    obj = root_object
    if isinstance(obj, dsl.MuranoObjectInterface):
        obj = obj.object
    parent = obj.owner if isinstance(obj,  dsl_types.MuranoObject) else None
    while True:
        obj, need_another_pass = _pass12_serialize(
            obj, parent, serialized_objects, designer_attributes, executor,
            serialize_actions, serialization_type, allow_refs,
            with_destruction_dependencies)
        if not need_another_pass:
            break
    tree = [obj]
    _pass3_serialize(tree, serialized_objects, allow_refs)
    return tree[0], serialized_objects


def serialize_model(root_object, executor,
                    allow_refs=False,
                    make_copy=True,
                    serialize_attributes=True,
                    serialize_actions=True,
                    serialization_type=dsl_types.DumpTypes.Serializable,
                    with_destruction_dependencies=True):
    designer_attributes = executor.object_store.designer_attributes

    if root_object is None:
        tree = None
        tree_copy = None
        attributes = []
    else:
        with helpers.with_object_store(executor.object_store):
            tree, serialized_objects = _serialize_object(
                root_object, designer_attributes, allow_refs, executor,
                serialize_actions, serialization_type,
                with_destruction_dependencies)

            tree_copy = _serialize_object(
                root_object, None, allow_refs, executor, serialize_actions,
                serialization_type,
                with_destruction_dependencies)[0] if make_copy else None

            attributes = executor.attribute_store.serialize(
                serialized_objects) if serialize_attributes else None

    return {
        'Objects': tree,
        'ObjectsCopy': tree_copy,
        'Attributes': attributes
    }


def _serialize_available_action(obj, current_actions, executor):
    result = {}
    actions = obj.type.find_methods(lambda m: m.is_action)
    for action in actions:
        action_id = '{0}_{1}'.format(obj.object_id, action.name)
        entry = current_actions.get(action_id, {'enabled': True})
        entry['name'] = action.name
        context = executor.create_type_context(action.declaring_type)
        meta = action.get_meta(context)
        meta_dict = {item.type.name: item for item in meta}
        title = meta_dict.get('io.murano.metadata.Title')
        if title:
            entry['title'] = title.get_property('text')
        else:
            entry['title'] = action.name
        description = meta_dict.get('io.murano.metadata.Description')
        if description:
            entry['description'] = description.get_property('text')
        help_text = meta_dict.get('io.murano.metadata.HelpText')
        if help_text:
            entry['helpText'] = help_text.get_property('text')
        result[action_id] = entry
    return result


def _pass12_serialize(value, parent, serialized_objects,
                      designer_attributes_getter, executor,
                      serialize_actions, serialization_type, allow_refs,
                      with_destruction_dependencies):
    if isinstance(value, dsl.MuranoObjectInterface):
        value = value.object
    if isinstance(value, (six.string_types,
                          int, float, bool)) or value is None:
        return value, False
    if isinstance(value, dsl_types.MuranoObject):
        if value.owner is not parent or value.object_id in serialized_objects:
            return ObjRef(value), True
    elif isinstance(value, ObjRef):
        can_move = value.ref_obj.object_id not in serialized_objects
        if can_move and allow_refs and value.ref_obj.owner is not None:
            can_move = (is_nested_in(parent, value.ref_obj.owner) and
                        value.ref_obj.owner.object_id in serialized_objects)
        if can_move:
            value = value.ref_obj
        else:
            return value, False
    if isinstance(value, (dsl_types.MuranoType,
                          dsl_types.MuranoTypeReference)):
        return helpers.format_type_string(value), False
    if helpers.is_passkey(value):
        return value, False
    if isinstance(value, dsl_types.MuranoObject):
        result = value.to_dictionary(
            serialization_type=serialization_type, allow_refs=allow_refs,
            with_destruction_dependencies=with_destruction_dependencies)
        if designer_attributes_getter is not None:
            if serialization_type == dsl_types.DumpTypes.Inline:
                system_data = result
            else:
                system_data = result['?']
            system_data.update(designer_attributes_getter(value.object_id))
            if serialize_actions:
                # deserialize and merge list of actions
                system_data['_actions'] = _serialize_available_action(
                    value, system_data.get('_actions', {}), executor)
        serialized_objects.add(value.object_id)
        return _pass12_serialize(
            result, value, serialized_objects, designer_attributes_getter,
            executor, serialize_actions, serialization_type, allow_refs,
            with_destruction_dependencies)
    elif isinstance(value, utils.MappingType):
        result = {}
        need_another_pass = False

        for d_key, d_value in value.items():
            if (isinstance(d_key, dsl_types.MuranoType) and
                    serialization_type == dsl_types.DumpTypes.Serializable):
                result_key = str(d_key)
            else:
                result_key = d_key
            if (result_key == 'type' and
                    isinstance(d_value, dsl_types.MuranoType) and
                    serialization_type == dsl_types.DumpTypes.Mixed):
                result_value = d_value, False
            else:
                result_value = _pass12_serialize(
                    d_value, parent, serialized_objects,
                    designer_attributes_getter, executor, serialize_actions,
                    serialization_type, allow_refs,
                    with_destruction_dependencies)
            result[result_key] = result_value[0]
            if result_value[1]:
                need_another_pass = True
        return result, need_another_pass
    elif utils.is_sequence(value) or isinstance(value, utils.SetType):
        need_another_pass = False
        result = []
        for t in value:
            v, nmp = _pass12_serialize(
                t, parent, serialized_objects, designer_attributes_getter,
                executor, serialize_actions, serialization_type, allow_refs,
                with_destruction_dependencies)
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


def collect_objects(root_object):
    visited = set()

    def rec(obj):
        if utils.is_sequence(obj) or isinstance(obj, utils.SetType):
            for value in obj:
                for t in rec(value):
                    yield t
        elif isinstance(obj, utils.MappingType):
            for value in obj.values():
                for t in rec(value):
                    yield t
        elif isinstance(obj, dsl_types.MuranoObjectInterface):
                for t in rec(obj.object):
                    yield t
        elif isinstance(obj, dsl_types.MuranoObject) and obj not in visited:
            visited.add(obj)
            yield obj
            for t in rec(obj.to_dictionary()):
                yield t

    return rec(root_object)
