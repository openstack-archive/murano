# Copyright (c) 2014 OpenStack Foundation.
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


class CongressRulesManager(object):
    """Converts murano model to list of congress rules:
        - murano:objects+(env_id, obj_id, type_name)
        - murano:properties+(obj_id, prop_name, prop_value)
        - murano:relationships+(source, target, name)
        - murano:parent_types+(obj_id, parent_name)
        - murano:states+(env_id, state)
    """

    _rules = []
    _env_id = ''
    _class_loader = None

    def convert(self, model, class_loader=None, tenant_id=None):
        self._rules = []
        self._class_loader = class_loader

        if model is None:
            return self._rules

        self._env_id = model['?']['id']

        # Arbitrary property for tenant_id.
        if tenant_id is not None:
            r = PropertyRule(self._env_id, 'tenant_id', tenant_id)
            self._rules.append(r)

        state_rule = StateRule(self._env_id, 'PENDING')
        self._rules.append(state_rule)

        self._walk(model, self._process_item)

        # Convert MuranoProperty containing reference to another object
        # to MuranoRelationship.
        object_ids = [rule.obj_id for rule in self._rules
                      if isinstance(rule, ObjectRule)]

        self._rules = [self._create_relationship(rule, object_ids)
                       for rule in self._rules]

        return self._rules

    def _walk(self, obj, func):

        if obj is None:
            return

        obj = self._to_dict(obj)
        func(obj)
        if isinstance(obj, list):
            for v in obj:
                self._walk(v, func)
        elif isinstance(obj, dict):
            for key, value in obj.iteritems():
                self._walk(value, func)

    def _process_item(self, obj):
        if isinstance(obj, dict) and '?' in obj:
            obj2 = self._create_object_rule(obj, self._env_id)
            self._rules.append(obj2)
            self._rules.extend(self._create_propety_rules(obj2.obj_id, obj))

            cls = obj['?']['type']
            types = self._get_parent_types(cls, self._class_loader)
            self._rules.extend(self._create_parent_type_rules(obj['?']['id'],
                                                              types))

    @staticmethod
    def _to_dict(obj):
        # If we have MuranoObject class we need to convert to dictionary.
        if 'to_dictionary' in dir(obj):
            return obj.to_dictionary()
        else:
            return obj

    @staticmethod
    def _create_object_rule(app, env_id):
        return ObjectRule(app['?']['id'], env_id, app['?']['type'])

    def _create_propety_rules(self, obj_id, obj, prefix=""):
        rules = []

        # Skip when inside properties of other object.
        if '?' in obj and prefix != "":
            rules.append(RelationshipRule(obj_id, obj['?']['id'],
                                          prefix.split('.')[0]))
            return rules

        for key, value in obj.iteritems():
            if key == '?':
                continue

            if value is None:
                value = ""

            value = self._to_dict(value)
            if isinstance(value, dict):
                rules.extend(self._create_propety_rules(
                    obj_id, value, prefix + key + "."))
            elif isinstance(value, list):
                for v in value:
                    v = self._to_dict(v)
                    if not isinstance(v, dict):
                        rule = PropertyRule(obj_id, prefix + key, v)
                        rules.append(rule)
            else:
                rule = PropertyRule(obj_id, prefix + key, value)
                rules.append(rule)

        return rules

    @staticmethod
    def _is_relationship(rule, app_ids):
        if not isinstance(rule, PropertyRule):
            return False

        return rule.prop_value in app_ids

    def _create_relationship(self, rule, app_ids):
        if self._is_relationship(rule, app_ids):
            return RelationshipRule(rule.obj_id, rule.prop_value,
                                    rule.prop_name)
        else:
            return rule

    def _get_parent_types(self, type_name, class_loader):
        types = set()
        types.add(type_name)
        if class_loader is not None:
            cls = class_loader.get_class(type_name)
            if cls is not None:
                for parent in cls.parents:
                    types.add(parent.name)
                    types = types.union(
                        self._get_parent_types(parent.name, class_loader))
        return types

    @staticmethod
    def _create_parent_type_rules(app_id, types):
        rules = []
        for type_name in types:
            rules.append(ParentTypeRule(app_id, type_name))
        return rules


class ObjectRule(object):
    def __init__(self, obj_id, env_id, type_name):
        self.obj_id = obj_id
        self.env_id = env_id
        self.type_name = type_name

    def __str__(self):
        return 'murano:objects+("{0}", "{1}", "{2}")'.format(self.obj_id,
                                                             self.env_id,
                                                             self.type_name)


class PropertyRule(object):
    def __init__(self, obj_id, prop_name, prop_value):
        self.obj_id = obj_id
        self.prop_name = prop_name
        self.prop_value = prop_value

    def __str__(self):
        return 'murano:properties+("{0}", "{1}", "{2}")'.format(
            self.obj_id, self.prop_name, self.prop_value)


class RelationshipRule(object):
    def __init__(self, source_id, target_id, rel_name):
        self.source_id = source_id
        self.target_id = target_id
        self.rel_name = rel_name

    def __str__(self):
        return 'murano:relationships+("{0}", "{1}", "{2}")'.format(
            self.source_id, self.target_id, self.rel_name)


class ParentTypeRule(object):
    def __init__(self, obj_id, type_name):
        self.obj_id = obj_id
        self.type_name = type_name

    def __str__(self):
        return 'murano:parent_types+("{0}", "{1}")'.format(self.obj_id,
                                                           self.type_name)


class StateRule(object):
    def __init__(self, obj_id, state):
        self.obj_id = obj_id
        self.state = state

    def __str__(self):
        return 'murano:states+("{0}", "{1}")'.format(self.obj_id, self.state)