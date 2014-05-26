# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os.path

import yaml

import murano.dsl.class_loader as class_loader
import murano.dsl.yaql_expression as yaql_expression
import murano.engine.system.yaql_functions as yaql_functions


def yaql_constructor(loader, node):
    value = loader.construct_scalar(node)
    return yaql_expression.YaqlExpression(value)

yaml.add_constructor(u'!yaql', yaql_constructor)
yaml.add_implicit_resolver(u'!yaql', yaql_expression.YaqlExpression)


class SimpleClassLoader(class_loader.MuranoClassLoader):
    def __init__(self, base_path):
        self._base_path = base_path
        super(SimpleClassLoader, self).__init__()

    def load_definition(self, name):
        path = os.path.join(self._base_path, name, 'manifest.yaml')
        if not os.path.exists(path):
            return None
        with open(path) as stream:
            return yaml.load(stream)

    def create_root_context(self):
        context = super(SimpleClassLoader, self).create_root_context()
        yaql_functions.register(context)
        return context
