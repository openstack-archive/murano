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

from murano.dsl import helpers


class CongressRulesManager(object):
    """Converts murano model to list of congress rules

    The Congress rules are:
        - murano:objects+(env_id, obj_id, type_name)
        - murano:properties+(obj_id, prop_name, prop_value)
        - murano:relationships+(source, target, name)
        - murano:parent_types+(obj_id, parent_name)
        - murano:states+(env_id, state)
    """

    _rules = []
    _env_id = ''
    _package_loader = None

    def convert(self, model, package_loader=None, tenant_id=None):
        self._rules = []
        self._package_loader = package_loader

        if model is None:
            return self._rules

        self._env_id = model['?']['id']

        state_rule = StateRule(self._env_id, 'pending')
        self._rules.append(state_rule)

        self._walk(model, owner_id=tenant_id)

        # Convert MuranoProperty containing reference to another object
        # to MuranoRelationship.
        object_ids = [rule.obj_id for rule in self._rules
                      if isinstance(rule, ObjectRule)]

        self._rules = [self._create_relationship(rule, object_ids)
                       for rule in self._rules]

        relations = [(rel.source_id, rel.target_id)
                     for rel in self._rules
                     if isinstance(rel, RelationshipRule)]
        closure = self.transitive_closure(relations)

        for rel in closure:
            self._rules.append(ConnectedRule(rel[0], rel[1]))

        return self._rules

    @staticmethod
    def transitive_closure(relations):
        """Computes transitive closure on a directed graph.

        In other words computes reachability within the graph.
        E.g. {(1, 2), (2, 3)} -> {(1, 2), (2, 3), (1, 3)}
        (1, 3) was added because there is path from 1 to 3 in the graph.

        :param relations: list of relations/edges in form of tuples
        :return: transitive closure including original relations
        """
        closure = set(relations)
        while True:
            # Attempts to discover new transitive relations
            # by joining 2 subsequent relations/edges within the graph.
            new_relations = {(x, w) for x, y in closure
                             for q, w in closure if q == y}
            # Creates union with already discovered relations.
            closure_until_now = closure | new_relations
            # If no new relations were discovered in last cycle
            # the computation is finished.
            if closure_until_now == closure:
                return closure
            closure = closure_until_now

    def _walk(self, obj, owner_id, path=()):

        if obj is None:
            return

        obj = self._to_dict(obj)
        new_owner = self._process_item(obj, owner_id, path) or owner_id
        if isinstance(obj, list) or isinstance(obj, tuple):
            for v in obj:
                self._walk(v, new_owner, path)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                self._walk(value, new_owner, path + (key, ))

    def _process_item(self, obj, owner_id, path):
        if isinstance(obj, dict) and '?' in obj:
            obj_rule = self._create_object_rule(obj, owner_id)

            self._rules.append(obj_rule)
            # the environment has 'services' relationships
            # to all its top-level applications
            # traversal path is used to test whether
            # we are at the right place within the tree
            if path == ('applications',):
                self._rules.append(RelationshipRule(self._env_id,
                                                    obj_rule.obj_id,
                                                    "services"))
            self._rules.extend(
                self._create_property_rules(obj_rule.obj_id, obj))

            cls = obj['?']['type']
            if 'classVersion' in obj['?']:
                version_spec = obj['?']['classVersion']
            else:
                version_spec = '*'
            types = self._get_parent_types(
                cls, self._package_loader, version_spec)
            self._rules.extend(self._create_parent_type_rules(obj['?']['id'],
                                                              types))
            # current object will be the owner for its subtree
            return obj_rule.obj_id

    @staticmethod
    def _to_dict(obj):
        # If we have MuranoObject class we need to convert to dictionary.
        if 'to_dictionary' in dir(obj):
            return obj.to_dictionary()
        else:
            return obj

    def _create_object_rule(self, app, owner_id):
        return ObjectRule(app['?']['id'], owner_id, app['?']['type'])

    def _create_property_rules(self, obj_id, obj, prefix=""):
        rules = []

        # Skip when inside properties of other object.
        if '?' in obj and prefix != "":
            rules.append(RelationshipRule(obj_id, obj['?']['id'],
                                          prefix.split('.')[0]))
            return rules

        for key, value in obj.items():
            if key == '?':
                continue

            if value is not None:
                value = self._to_dict(value)
                if isinstance(value, dict):
                    rules.extend(self._create_property_rules(
                        obj_id, value, prefix + key + "."))
                elif isinstance(value, list) or isinstance(obj, tuple):
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

    @staticmethod
    def _get_parent_types(type_name, package_loader, version_spec):
        type_name, version_spec, _ = helpers.parse_type_string(
            type_name, version_spec, None)
        version_spec = helpers.parse_version_spec(version_spec)
        result = {type_name}
        if package_loader:
            pkg = package_loader.load_class_package(type_name, version_spec)
            cls = pkg.find_class(type_name, False)
            if cls:
                result.update(t.name for t in cls.ancestors())
        return result

    @staticmethod
    def _create_parent_type_rules(app_id, types):
        rules = []
        for type_name in types:
            rules.append(ParentTypeRule(app_id, type_name))
        return rules


class ObjectRule(object):
    def __init__(self, obj_id, owner_id, type_name):
        self.obj_id = obj_id
        self.owner_id = owner_id
        self.type_name = helpers.parse_type_string(type_name, None, None)[0]

    def __str__(self):
        return 'murano:objects+("{0}", "{1}", "{2}")'.format(self.obj_id,
                                                             self.owner_id,
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


class ConnectedRule(object):
    def __init__(self, source_id, target_id):
        self.source_id = source_id
        self.target_id = target_id

    def __str__(self):
        return 'murano:connected+("{0}", "{1}")'.format(
            self.source_id, self.target_id)


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
