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
import yaml.composer
import yaml.constructor

from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.dsl import yaql_expression


@helpers.memoize
def get_loader(version):
    version = helpers.parse_version(version)

    class MuranoPlDict(dict):
        pass

    class YaqlExpression(yaql_expression.YaqlExpression):
        @staticmethod
        def match(expr):
            return yaql_expression.YaqlExpression.is_expression(expr, version)

    def load(contents, file_id):
        def build_position(node):
            return dsl_types.ExpressionFilePosition(
                file_id,
                node.start_mark.line + 1,
                node.start_mark.column + 1,
                node.end_mark.line + 1,
                node.end_mark.column + 1)

        class MuranoPlYamlConstructor(yaml.constructor.SafeConstructor):
            def construct_yaml_map(self, node):
                data = MuranoPlDict()
                data.source_file_position = build_position(node)
                yield data
                value = self.construct_mapping(node)
                data.update(value)

        class YaqlYamlLoader(yaml.SafeLoader, MuranoPlYamlConstructor):
            pass

        YaqlYamlLoader.add_constructor(
            u'tag:yaml.org,2002:map',
            MuranoPlYamlConstructor.construct_yaml_map)

        # workaround for PyYAML bug: http://pyyaml.org/ticket/221
        resolvers = {}
        for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items():
            resolvers[k] = v[:]
        YaqlYamlLoader.yaml_implicit_resolvers = resolvers

        def yaql_constructor(loader, node):
            value = loader.construct_scalar(node)
            result = yaql_expression.YaqlExpression(value, version)
            result.source_file_position = build_position(node)
            return result

        YaqlYamlLoader.add_constructor(u'!yaql', yaql_constructor)
        YaqlYamlLoader.add_implicit_resolver(u'!yaql', YaqlExpression, None)
        return list(filter(
            lambda t: t,
            yaml.load_all(contents, Loader=YaqlYamlLoader))
        )

    return load
