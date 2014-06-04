# Copyright (c) 2014 Mirantis Inc.
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

import yaml

from murano.dsl import yaql_expression


class YaqlYamlLoader(yaml.Loader):
    pass

# workaround for PyYAML bug: http://pyyaml.org/ticket/221
resolvers = {}
for k, v in yaml.Loader.yaml_implicit_resolvers.items():
    resolvers[k] = v[:]
YaqlYamlLoader.yaml_implicit_resolvers = resolvers


def yaql_constructor(loader, node):
    value = loader.construct_scalar(node)
    result = yaql_expression.YaqlExpression(value)
    position = yaql_expression.YaqlExpressionFilePosition(
        node.start_mark.name,
        node.start_mark.line + 1,
        node.start_mark.column + 1,
        node.start_mark.index,
        node.end_mark.line + 1,
        node.end_mark.column + 1,
        node.end_mark.index - node.start_mark.index)
    result.file_position = position
    return result

yaml.add_constructor(u'!yaql', yaql_constructor, YaqlYamlLoader)
yaml.add_implicit_resolver(u'!yaql', yaql_expression.YaqlExpression,
                           Loader=YaqlYamlLoader)
