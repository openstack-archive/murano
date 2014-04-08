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

import types

import muranoapi.dsl.murano_object as murano_object


class ObjRef(object):
    def __init__(self, obj):
        self.ref_obj = obj


def serialize(root_object, executor):
    if root_object is None:
        tree = None
        attributes = []
    else:
        serialized_objects = set()
        tree = _pass1_serialize(root_object, None, serialized_objects)
        _pass2_serialize(tree, serialized_objects)
        attributes = executor.attribute_store.serialize(serialized_objects)

    return {
        'Objects': tree,
        'ObjectsCopy': tree,
        'Attributes': attributes
    }


def _cmp_objects(obj1, obj2):
    if obj1 is None and obj2 is None:
        return True
    if obj1 is None or obj2 is None:
        return False
    return obj1.object_id == obj2.object_id


def _pass1_serialize(value, parent, serialized_objects):
    if isinstance(value, (types.StringTypes, types.IntType, types.FloatType,
                          types.BooleanType, types.NoneType)):
        return value
    elif isinstance(value, murano_object.MuranoObject):
        if not _cmp_objects(value.parent, parent) \
                or value.object_id in serialized_objects:
            return ObjRef(value)
        else:
            result = value.to_dictionary()
            serialized_objects.add(value.object_id)
            return _pass1_serialize(result, value, serialized_objects)

    elif isinstance(value, types.DictionaryType):
        result = {}
        for d_key, d_value in value.iteritems():
            result_key = str(d_key)
            result[result_key] = _pass1_serialize(
                d_value, parent, serialized_objects)
        return result
    elif isinstance(value, types.ListType):
        return [_pass1_serialize(t, parent, serialized_objects) for t in value]
    elif isinstance(value, types.TupleType):
        return _pass1_serialize(list(value), parent, serialized_objects)
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
