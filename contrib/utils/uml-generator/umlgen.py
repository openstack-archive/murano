#!/usr/bin/python
#    Copyright (c) 2013 Mirantis, Inc.
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

import argparse
import os
import re
import yaml


# Workaround for unknown yaml tags
def yaml_default_ctor(loader, tag_suffix, node):
    return tag_suffix + ' ' + node.value

yaml.add_multi_constructor('', yaml_default_ctor)


class PlantUmlNode():
    def __init__(self, node_dn):
        self._dn = node_dn
        self.attributes = []
        self.operations = []
        self.extras = []

    def write(self, f):
        f.write('class {0} {{\n'.format(self._dn))
        f.write('-- Properties --\n')
        for item in self.attributes:
            f.write('<{type}> {name}: {contract}\n'.format(**item))
        f.write('-- Workflows --\n')
        for item in self.operations:
            f.write('{name}()\n'.format(**item))
        f.write('-- Namespaces --\n')
        for item in self.extras:
            if item['key'] != '=':
                f.write('{key}: {value}\n'.format(**item))
        f.write('}\n')

    def add_attribute(self, name, type, contract):
        d = {'type': type, 'name': name, 'contract': contract}
        self.attributes.append(d)

    def add_operation(self, name):
        d = {'name': name}
        self.operations.append(d)

    def add_extra(self, key, value):
        d = {'key': key, 'value': value}
        self.extras.append(d)


class DslSpec():
    def __init__(self, class_dn, basepath='.'):
        self._dn = class_dn
        self._id = self._dn.replace('.', '_')
        self._name = self._dn.split('.')[-1]
        self._ns = ('=', self._dn.split('.')[:-1])
        self._graph = None
        self.is_virtual = True
        self.parent_dn = None
        self.manifest = None

        manifest_path = os.path.join(basepath, self._dn, 'manifest.yaml')
        if os.path.exists(manifest_path):
            self.manifest = yaml.load(open(manifest_path))

        if self.manifest:
            self.is_virtual = False
            self.name = self.manifest['Name']
            if 'Extends' in self.manifest:
                self.parent_dn = self.get_dn(self.manifest['Extends'])

    def split_ns(self, name=None):
        if name:
            parts = name.split(':')
            if len(parts) == 1:
                parts.insert(0, '=')
        else:
            parts = ['=', self._name]
        return parts

    def get_ns(self, name=None):
        parts = self.split_ns(name)
        return {
            'key': parts[0],
            'value': self.manifest['Namespaces'][parts[0]]
        }

    def get_dn(self, name=None):
        parts = self.split_ns(name)
        parts[0] = self.get_ns(parts[0] + ':')['value']
        return '.'.join(parts)

    def get_name(self):
        return self._name


class DslPlantUmlNode(DslSpec):
    def write(self, file):
        uml_class = PlantUmlNode(self._dn)
        ext_classes = []
        if not self.is_virtual:
            namespaces = [self.get_ns()]
            for name, item in self.manifest.get('Properties', {}).iteritems():
                item_type = item.get('Type', 'In')
                item_contract = str(item.get('Contract', 'UNDEFINED'))
                match = re.search('class\((.*?)\)', item_contract)
                if match:
                    ns = self.get_ns(match.group(1))
                    ext_classes.append(self.get_dn(match.group(1)))
                    if not ns in namespaces:
                        namespaces.append(ns)
                uml_class.add_attribute(
                    name,
                    type=item_type,
                    contract=item_contract
                )
            for m in self.manifest.get('Workflow', []):
                uml_class.add_operation(m)
            for ns in namespaces:
                uml_class.add_extra(ns['key'], ns['value'])
        uml_class.write(file)
        return ext_classes


class DslPlantUmlGraph():
    def __init__(self):
        self._nodes = []
        self._edges = []
        self._options = {}
        self._file = None

    def write(self, classname, level=0):
        if level == 0:
            self._file.write('@startuml\n')
            if self.get_option('NoNamespaces', False):
                self._file.write('set namespaceSeparator none\n')

        if self.node_exists(classname):
            return

        self.add_node(classname)

        node = DslPlantUmlNode(classname)
        ext_classes = node.write(self._file)

        if not self.get_option('ParentsOnly', False):
            for ext_class in ext_classes:
                self.add_edge(
                    from_node=ext_class,
                    to_node=classname,
                    edge_type='<..'
                )
                self.write(ext_class, level + 1)

        if node.is_virtual:
            return

        if node.parent_dn:
            self.add_edge(
                from_node=node.parent_dn,
                to_node=classname,
                edge_type='<|--'
            )
            self.write(node.parent_dn, level + 1)

        if level == 0:
            for edge in self._edges:
                self._file.write('{from_node} {type} {to_node}\n'
                    .format(**edge))
            self._file.write('@enduml\n')
            self._file.close()

    def add_node(self, classname):
        self._nodes.append(classname)

    def node_exists(self, dn):
        return dn in self._nodes

    def add_edge(self, from_node, to_node, edge_type):
        edge = {'from_node': from_node, 'to_node': to_node, 'type': edge_type}
        if not edge in self._edges:
            self._edges.append(edge)

    def set_option(self, key, value):
        self._options[key] = value

    def get_option(self, key, default=None):
        return self._options.get(key, default)

    def open_file(self, file_name):
        self._file = open(file_name, 'w')

    def close_file(self):
        self._file.close()


parser = argparse.ArgumentParser(description='Qwerty')
parser.add_argument('classname',
                    default='com.mirantis.murano.demoApp.DemoHost',
                    help='Dsl Class Name to draw.', nargs='?')
parser.add_argument('-n', '--no-namespaces', action='store_true')
parser.add_argument('-p', '--parents-only', action='store_true')
args = parser.parse_args()

graph = DslPlantUmlGraph()
graph.set_option('NoNamespaces', args.no_namespaces)
graph.set_option('ParentsOnly', args.parents_only)
graph.open_file('plantuml.txt')
graph.write(args.classname)
graph.close_file()

os.system('java -jar plantuml.jar plantuml.txt')
os.system('xdg-open plantuml.png')
