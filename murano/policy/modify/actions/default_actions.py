# Copyright (c) 2015 OpenStack Foundation.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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

"""
Default actions reside in this module.
These action are available out of the box for Murano users.

"""
import yaql.language.utils as utils

import murano.dsl.exceptions as exceptions
import murano.dsl.murano_object as mo
import murano.policy.modify.actions.base as base


class ActionUtils(object):
    def _get_objects_by_id(self, obj, objects=None):
        if objects is None:
            objects = {}
        if isinstance(obj, mo.MuranoObject):
            objects[obj.object_id] = obj
            for prop_name in obj.type.properties:
                try:
                    prop_val = obj.get_property(prop_name)
                except exceptions.UninitializedPropertyAccessError:
                    continue
                self._get_objects_by_id(prop_val, objects)
        elif isinstance(obj, tuple):
            for item in obj:
                self._get_objects_by_id(item, objects)
        elif isinstance(obj, utils.FrozenDict):
            for k, v in obj.items():
                self._get_objects_by_id(k, objects)
                self._get_objects_by_id(v, objects)
        return objects

    @staticmethod
    def _check_present(obj_id, objects):
        if obj_id not in objects.keys():
            raise ValueError('No such object, obj_id: {0}'
                             .format(obj_id))


class RemoveObjectAction(base.ModifyActionBase, ActionUtils):
    """Remove object from given model"""

    def __init__(self, object_id):
        """Initializes action parameters

        :param object_id: id of an object
        """
        self._object_id = object_id

    @staticmethod
    def _match_object_id(obj_id, obj):
        return isinstance(obj, mo.MuranoObject) and obj_id == obj.object_id

    def modify(self, obj):
        """Remove object from given model"""
        objects = self._get_objects_by_id(obj)
        self._check_present(self._object_id, objects)

        for _obj in objects.values():
            for prop_name in _obj.type.properties:
                try:
                    val = _obj.get_property(prop_name)
                except exceptions.UninitializedPropertyAccessError:
                    continue
                if self._match_object_id(self._object_id, val):
                    _obj.set_property(prop_name, None)
                # remove object from list
                elif isinstance(val, tuple):
                    filtered_list = list(val)
                    for item in val:
                        if self._match_object_id(self._object_id, item):
                            filtered_list.remove(item)
                    if len(filtered_list) < len(val):
                        _obj.set_property(prop_name, tuple(filtered_list))
                # remove object from dict
                elif isinstance(val, utils.FrozenDict):
                    filtered_dict = {k: v for k, v in val.items() if not
                                     self._match_object_id(self._object_id,
                                                           k) and not
                                     self._match_object_id(self._object_id, v)}
                    if len(filtered_dict) < len(val):
                        _obj.set_property(prop_name,
                                          utils.FrozenDict(filtered_dict))


class SetPropertyAction(base.ModifyActionBase, ActionUtils):
    """Set property on given object"""

    def __init__(self, object_id, prop_name, value):
        """Initializes action parameters

        :param object_id: id of an object
        :param prop_name: property name
        :param value: new value of the property
        """
        self._object_id = object_id
        self._prop_name = prop_name
        self._value = value

    def modify(self, obj):
        """Set property on given object in model"""
        objects = self._get_objects_by_id(obj)
        self._check_present(self._object_id, objects)
        target_obj = objects[self._object_id]
        target_obj.set_property(self._prop_name, self._value)


class RemoveRelationAction(SetPropertyAction):
    """Remove relation from given model"""

    def __init__(self, object_id, prop_name):
        super(RemoveRelationAction, self).__init__(object_id, prop_name, None)


class AddObjectAction(base.ModifyActionBase, ActionUtils):
    """Add new object to object model"""

    def __init__(self, owner_id, owner_relation, type, init_args):
        """Initializes action parameters

        :param owner_id: id of an owner
        :param owner_relation: name of relation on owner
        :param type: new object type
        :param init_args: properties of the new object
        """
        self._init_args = init_args
        self._type = type
        self._owner_relation = owner_relation
        self._owner_id = owner_id

    def modify(self, model):
        """Creates new object and adds it to the model"""
        new_obj = {'type': type}
        new_obj.update(self._init_args)
        objects = self._get_objects_by_id(model)
        self._check_present(self._owner_id, objects)
        owner = objects[self._owner_id]
        # adding objects to list or dict is not supported for now
        owner.set_property(self._owner_relation, new_obj)


class AddRelationAction(base.ModifyActionBase, ActionUtils):
    """Adds relation between two existing objects within model"""

    def __init__(self, source_id, relation, target_id):
        """Initializes action parameters

        :param source_id: id of an relation source
        :param relation: name of relation on source object
        :param target_id: id of an relation target
        """
        self._source_id = source_id
        self._relation = relation
        self._target_id = target_id

    def modify(self, model):
        """Creates new object and adds it to the model"""
        objects = self._get_objects_by_id(model)
        self._check_present(self._source_id, objects)
        self._check_present(self._target_id, objects)
        source = objects[self._source_id]
        target = objects[self._target_id]
        # adding objects to list or dict is not supported for now
        source.set_property(self._relation, target)
