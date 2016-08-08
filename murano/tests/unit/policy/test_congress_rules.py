# Copyright (c) 2014 OpenStack Foundation.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import inspect
import os.path

import unittest2 as unittest
import yaml

from murano.common import uuidutils
from murano.dsl import helpers
from murano.dsl import package_loader
import murano.policy.congress_rules as congress

TENANT_ID = 'de305d5475b4431badb2eb6b9e546013'


class MockPackageLoader(package_loader.MuranoPackageLoader):
    def __init__(self, rules):
        """Create rules like this: ['child->parent', 'child->parent2']."""

        self._classes = {}
        rules_dict = {}
        for rule in rules:
            split = rule.split('->')
            rules_dict.setdefault(split[0], []).append(split[1])
        classes = (self.get_class(cls, rules_dict) for cls in rules_dict)
        self._package = MockPackage(classes)

    def get_class(self, name, rules_dict):
        if name in self._classes:
            return self._classes[name]
        parents = [self.get_class(parent, rules_dict)
                   for parent in rules_dict.get(name, [])]
        result = MockClass({'name': name, 'declared_parents': parents})
        self._classes[name] = result
        return result

    def register_package(self, package):
        pass

    def load_class_package(self, class_name, version_spec):
        return self._package

    def load_package(self, package_name, version_spec):
        return self._package

    def export_fixation_table(self):
        pass

    def import_fixation_table(self, fixations):
        pass

    def compact_fixation_table(self):
        pass


class MockPackage(object):
    def __init__(self, classes):
        self._classes = {}
        for cls in classes:
            self._classes[cls.name] = cls

    @property
    def classes(self):
        return self._classes.keys()

    def find_class(self, name, *args, **kwargs):
        return self._classes.get(name)


class MockClass(object):
    def __init__(self, entries):
        self.__dict__.update(entries)

    def ancestors(self):
        return helpers.traverse(self, lambda t: t.declared_parents)


class TestCongressRules(unittest.TestCase):

    def _load_file(self, file_name):
        model_file = os.path.join(
            os.path.dirname(inspect.getfile(self.__class__)), file_name)

        with open(model_file) as stream:
            return yaml.safe_load(stream)

    def _create_rules_str(self, model_file, package_loader=None):
        model = self._load_file(model_file)

        congress_rules = congress.CongressRulesManager()
        rules = congress_rules.convert(model, package_loader,
                                       tenant_id=TENANT_ID)
        rules_str = ", \n".join(map(str, rules))

        return rules_str

    def test_transitive_closure(self):
        closure = congress.CongressRulesManager.transitive_closure(
            [(1, 2), (2, 3), (3, 4)])
        self.assertIn((1, 4), closure)
        self.assertIn((2, 4), closure)

    def test_empty_model(self):
        congress_rules = congress.CongressRulesManager()
        rules = congress_rules.convert(None)
        self.assertEqual(0, len(rules))

    def test_convert_simple_app(self):
        rules_str = self._create_and_check_rules_str('model')

        self.assertNotIn("instance.", rules_str)

    def test_convert_model_two_instances(self):
        rules_str = self._create_and_check_rules_str('model_two_instances')

        self.assertNotIn("\"instances\"", rules_str)

    def test_convert_model_with_relations(self):
        rules_str = self._create_rules_str('model_with_relations.yaml')

        self.assertNotIn(
            'murano:properties+("50fa68ff-cd9a-4845-b573-2c80879d158d", '
            '"server", "8ce94f23-f16a-40a1-9d9d-a877266c315d")', rules_str)

        self.assertIn(
            'murano:relationships+("50fa68ff-cd9a-4845-b573-2c80879d158d", '
            '"8ce94f23-f16a-40a1-9d9d-a877266c315d", "server")', rules_str)

        self.assertIn(
            'murano:relationships+("0aafd67e-72e9-4ae0-bb62-fe724f77df2a", '
            '"ed8df2b0-ddd2-4009-b3c9-2e7a368f3cb8", "instance")', rules_str)

    def test_convert_model_transitive_relationships(self):
        rules_str = self._create_rules_str('model_with_relations.yaml')

        self.assertIn(
            'murano:connected+("50fa68ff-cd9a-4845-b573-2c80879d158d", '
            '"8ce94f23-f16a-40a1-9d9d-a877266c315d")', rules_str)

        self.assertIn(
            'murano:connected+("8ce94f23-f16a-40a1-9d9d-a877266c315d", '
            '"fc6b8c41-166f-4fc9-a640-d82009e0a03d")', rules_str)

    def test_convert_model_services_relationship(self):
        rules_str = self._create_rules_str('model_with_relations.yaml')

        self.assertIn(
            'murano:relationships+("3409bdd0590e4c60b70fda5e6777ff96", '
            '"8ce94f23-f16a-40a1-9d9d-a877266c315d", "services")', rules_str)

        self.assertIn(
            'murano:relationships+("3409bdd0590e4c60b70fda5e6777ff96", '
            '"50fa68ff-cd9a-4845-b573-2c80879d158d", "services")', rules_str)

    def test_convert_model_complex(self):
        self._create_and_check_rules_str('model_complex')

    def test_convert_renamed_app(self):
        self._create_and_check_rules_str('model_renamed')

    def test_parent_types(self):

        #     grand-parent
        #       /     \
        #  parent1   parent2
        #       \     /
        # io.murano.apps.linux.Git

        package_loader = MockPackageLoader([
            'io.murano.apps.linux.Git->parent1',
            'io.murano.apps.linux.Git->parent2',
            'parent1->grand-parent',
            'parent2->grand-parent'
        ])

        rules_str = self._create_rules_str('model.yaml', package_loader)

        self.assertIn(
            'murano:parent_types+("0c810278-7282-4e4a-9d69-7b4c36b6ce6f",'
            ' "parent1")', rules_str)

        self.assertIn(
            'murano:parent_types+("0c810278-7282-4e4a-9d69-7b4c36b6ce6f",'
            ' "parent2")', rules_str)

        self.assertIn(
            'murano:parent_types+("0c810278-7282-4e4a-9d69-7b4c36b6ce6f",'
            ' "grand-parent")', rules_str)

        self.assertIn(
            'murano:parent_types+("0c810278-7282-4e4a-9d69-7b4c36b6ce6f",'
            ' "io.murano.apps.linux.Git")', rules_str)

    def test_to_dictionary(self):
        """test to_dictionary

        If model contains object entry (not dict)
        we try to convert to dict using 'to_dictionary' method.
        """

        class Struct(object):
            def __init__(self, d):
                self.__dict__ = d

            def to_dictionary(self):
                return self.__dict__

            def __getitem__(self, item):
                return self.__dict__[item]

        d = {'?': {'id': '1', 'type': 't1'},
             'apps': [Struct({'?': {'id': '2', 'type': 't2'},
                              'instances': [Struct(
                                  {'?': {'id': '3', 'type': 't3'}})]})]
             }

        model = Struct(d)

        congress_rules = congress.CongressRulesManager()
        tenant_id = uuidutils.generate_uuid()
        rules = congress_rules.convert(model, tenant_id=tenant_id)
        rules_str = ", \n".join(map(str, rules))

        self.assertIn('murano:objects+("1", "{0}", "t1")'.format(tenant_id),
                      rules_str)
        self.assertIn('murano:objects+("2", "1", "t2")', rules_str)
        self.assertIn('murano:objects+("3", "2", "t3")', rules_str)

    def test_environment_owner(self):
        model = self._load_file("model.yaml")
        congress_rules = congress.CongressRulesManager()
        rules = congress_rules.convert(model, tenant_id='tenant1')
        rules_str = ", \n".join(map(str, rules))
        self.assertIn('murano:objects+("c86104748a0c4907b4c5981e6d3bce9f", '
                      '"tenant1", "io.murano.Environment")', rules_str)

    def test_wordpress(self):
        package_loader = MockPackageLoader([
            'io.murano.Environment->io.murano.Object',
            'io.murano.resources.NeutronNetwork->io.murano.resources.Network',
            'io.murano.resources.Network->io.murano.Object',
            'io.murano.databases.MySql->io.murano.databases.SqlDatabase',
            'io.murano.databases.MySql->io.murano.Application',
            'io.murano.databases.SqlDatabase->io.murano.Object',
            'io.murano.resources.LinuxInstance->io.murano.resources.Instance',
            'io.murano.resources.Instance->io.murano.Object',
            'io.murano.Application->io.murano.Object',
            'io.murano.apps.apache.ApacheHttpServer->io.murano.Application',
            'io.murano.apps.ZabbixServer->io.murano.Application',
            'io.murano.apps.ZabbixAgent->io.murano.Application',
            'io.murano.apps.WordPress->io.murano.Application',

            'io.murano.resources.LinuxMuranoInstance->'
            'io.murano.resources.LinuxInstance'
        ])

        self._create_and_check_rules_str('wordpress', package_loader)

    def _create_and_check_rules_str(self, model_name, package_loader=None):
        rules_str = self._create_rules_str(
            '{0}.yaml'.format(model_name), package_loader)
        self._check_expected_rules(rules_str,
                                   'expected_rules_{0}.txt'.format(model_name))
        return rules_str

    def _check_expected_rules(self, rules_str, expected_rules_file_name):
        expected_rules_file = os.path.join(
            os.path.dirname(inspect.getfile(self.__class__)),
            expected_rules_file_name)

        s = ''
        with open(expected_rules_file) as f:
            for line in f:
                line = line.rstrip('\n')
                if line not in rules_str:
                    s += 'Expected rule not found:\n\t' + line + '\n'

        if len(s) > 0:
            self.fail(s)

    def test_state_rule(self):
        rules_str = self._create_rules_str('model.yaml')

        self.assertIn(
            'murano:states+("c86104748a0c4907b4c5981e6d3bce9f", "pending")',
            rules_str)
