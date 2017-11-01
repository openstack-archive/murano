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

import os
import shutil
import sys

import six
import yaml

from murano.common.helpers import path
from murano.packages import exceptions
from murano.packages import package_base

RESOURCES_DIR_NAME = 'Resources/'
HOT_FILES_DIR_NAME = 'HotFiles/'
HOT_ENV_DIR_NAME = 'HotEnvironments/'


class YAQL(object):
    def __init__(self, expr):
        self.expr = expr


class Dumper(yaml.SafeDumper):
    pass


def yaql_representer(dumper, data):
    return dumper.represent_scalar(u'!yaql', data.expr)


Dumper.add_representer(YAQL, yaql_representer)


class HotPackage(package_base.PackageBase):
    def __init__(self, format_name, runtime_version, source_directory,
                 manifest):
        super(HotPackage, self).__init__(
            format_name, runtime_version, source_directory, manifest)

        self._translated_class = None
        self._source_directory = source_directory
        self._translated_ui = None

    @property
    def classes(self):
        return self.full_name,

    @property
    def requirements(self):
        return {}

    @property
    def ui(self):
        if not self._translated_ui:
            self._translated_ui = self._translate_ui()
        return self._translated_ui

    def get_class(self, name):
        if name != self.full_name:
            raise exceptions.PackageClassLoadError(
                name, 'Class not defined in this package')
        if not self._translated_class:
            self._translate_class()
        return self._translated_class, '<generated code>'

    def _translate_class(self):
        template_file = path.secure_join(
            self._source_directory, 'template.yaml')

        if not os.path.isfile(template_file):
            raise exceptions.PackageClassLoadError(
                self.full_name, 'File with class definition not found')

        shutil.copy(template_file, self.get_resource(self.full_name))
        with open(template_file) as stream:
            hot = yaml.safe_load(stream)
            if 'resources' not in hot:
                raise exceptions.PackageFormatError('Not a HOT template')
        translated = {
            'Name': self.full_name,
            'Extends': 'io.murano.Application'
        }

        hot_envs_path = path.secure_join(
            self._source_directory, RESOURCES_DIR_NAME, HOT_ENV_DIR_NAME)

        # if using hot environments, doing parameter validation with contracts
        # will overwrite the parameters in the hot environment.
        # don't validate parameters if hot environments exist.
        validate_hot_parameters = (not os.path.isdir(hot_envs_path) or
                                   not os.listdir(hot_envs_path))

        parameters = HotPackage._build_properties(hot, validate_hot_parameters)
        parameters.update(HotPackage._translate_outputs(hot))
        translated['Properties'] = parameters

        files = HotPackage._translate_files(self._source_directory)
        translated.update(HotPackage._generate_workflow(hot, files))

        # use default_style with double quote mark because by default PyYAML
        # doesn't put any quote marks ans as a result strings with e.g. dashes
        # may be interpreted as YAQL expressions upon load
        self._translated_class = yaml.dump(
            translated, Dumper=Dumper, default_style='"')

    @staticmethod
    def _build_properties(hot, validate_hot_parameters):
        result = {
            'generatedHeatStackName': {
                'Contract': YAQL('$.string()'),
                'Usage': 'Out'
            },
            'hotEnvironment': {
                'Contract': YAQL('$.string()'),
                'Usage': 'In'
            },
            'name': {
                'Contract': YAQL('$.string().notNull()'),
                'Usage': 'In',

            }
        }

        if validate_hot_parameters:
            params_dict = {}
            for key, value in (hot.get('parameters') or {}).items():
                param_contract = HotPackage._translate_param_to_contract(value)
                params_dict[key] = param_contract
            result['templateParameters'] = {
                'Contract': params_dict,
                'Default': {},
                'Usage': 'In'
            }
        else:
            result['templateParameters'] = {
                'Contract': {},
                'Default': {},
                'Usage': 'In'
            }

        return result

    @staticmethod
    def _translate_param_to_contract(value):
        contract = '$'

        parameter_type = value['type']
        if parameter_type in ('string', 'comma_delimited_list', 'json'):
            contract += '.string()'
        elif parameter_type == 'number':
            contract += '.int()'
        elif parameter_type == 'boolean':
            contract += '.bool()'
        else:
            raise ValueError('Unsupported parameter type ' + parameter_type)

        constraints = value.get('constraints') or []
        for constraint in constraints:
            translated = HotPackage._translate_constraint(constraint)
            if translated:
                contract += translated

        result = YAQL(contract)
        return result

    @staticmethod
    def _translate_outputs(hot):
        contract = {}
        for key in (hot.get('outputs') or {}).keys():
            contract[key] = YAQL("$.string()")
        return {
            'templateOutputs': {
                'Contract': contract,
                'Default': {},
                'Usage': 'Out'
            }
        }

    @staticmethod
    def _translate_files(source_directory):
        hot_files_path = path.secure_join(
            source_directory, RESOURCES_DIR_NAME, HOT_FILES_DIR_NAME)

        return HotPackage._build_hot_resources(hot_files_path)

    @staticmethod
    def _build_hot_resources(basedir):
        result = []
        if os.path.isdir(basedir):
            for root, _, files in os.walk(os.path.abspath(basedir)):
                for f in files:
                    full_path = path.secure_join(root, f)
                    relative_path = os.path.relpath(full_path, basedir)
                    result.append(relative_path)
        return result

    @staticmethod
    def _translate_constraint(constraint):
        if 'allowed_values' in constraint:
            return HotPackage._translate_allowed_values_constraint(
                constraint['allowed_values'])
        elif 'length' in constraint:
            return HotPackage._translate_length_constraint(
                constraint['length'])
        elif 'range' in constraint:
            return HotPackage._translate_range_constraint(
                constraint['range'])
        elif 'allowed_pattern' in constraint:
            return HotPackage._translate_allowed_pattern_constraint(
                constraint['allowed_pattern'])

    @staticmethod
    def _translate_allowed_pattern_constraint(value):
        return ".check(matches($, '{0}'))".format(value)

    @staticmethod
    def _translate_allowed_values_constraint(values):
        return '.check($ in list({0}))'.format(
            ', '.join([HotPackage._format_value(v) for v in values]))

    @staticmethod
    def _translate_length_constraint(value):
        if 'min' in value and 'max' in value:
            return '.check(len($) >= {0} and len($) <= {1})'.format(
                int(value['min']), int(value['max']))
        elif 'min' in value:
            return '.check(len($) >= {0})'.format(int(value['min']))
        elif 'max' in value:
            return '.check(len($) <= {0})'.format(int(value['max']))

    @staticmethod
    def _translate_range_constraint(value):
        if 'min' in value and 'max' in value:
            return '.check($ >= {0} and $ <= {1})'.format(
                int(value['min']), int(value['max']))
        elif 'min' in value:
            return '.check($ >= {0})'.format(int(value['min']))
        elif 'max' in value:
            return '.check($ <= {0})'.format(int(value['max']))

    @staticmethod
    def _format_value(value):
        if isinstance(value, six.string_types):
            return str("'" + value + "'")
        return str(value)

    @staticmethod
    def _generate_workflow(hot, files):
        hot_files_map = {}
        for f in files:
            file_path = "$resources.string('{0}{1}')".format(
                HOT_FILES_DIR_NAME, f)
            hot_files_map[f] = YAQL(file_path)

        hot_env = YAQL("$.hotEnvironment")

        deploy = [
            {YAQL('$environment'): YAQL(
                "$.find('io.murano.Environment').require()"
            )},
            {YAQL('$reporter'): YAQL(
                "new('io.murano.system.StatusReporter', "
                "environment => $environment)")},
            {
                'If': YAQL('$.getAttr(generatedHeatStackName) = null'),
                'Then': [
                    YAQL("$.setAttr(generatedHeatStackName, "
                         "'{0}_{1}'.format(randomName(), id($environment)))")
                ]
            },
            {YAQL('$stack'): YAQL(
                "new('io.murano.system.HeatStack', $environment, "
                "name => $.getAttr(generatedHeatStackName))")},

            YAQL("$reporter.report($this, "
                 "'Application deployment has started')"),

            {YAQL('$resources'): YAQL("new('io.murano.system.Resources')")},

            {YAQL('$template'): YAQL("$resources.yaml(type($this))")},
            YAQL('$stack.setTemplate($template)'),
            {YAQL('$parameters'): YAQL("$.templateParameters")},
            YAQL('$stack.setParameters($parameters)'),
            {YAQL('$files'): hot_files_map},
            YAQL('$stack.setFiles($files)'),
            {YAQL('$hotEnv'): hot_env},
            {
                'If': YAQL("bool($hotEnv)"),
                'Then': [
                    {YAQL('$envRelPath'): YAQL("'{0}' + $hotEnv".format(
                        HOT_ENV_DIR_NAME))},
                    {YAQL('$hotEnvContent'): YAQL("$resources.string("
                                                  "$envRelPath)")},
                    YAQL('$stack.setHotEnvironment($hotEnvContent)')
                ]
            },

            YAQL("$reporter.report($this, 'Stack creation has started')"),
            {
                'Try': [YAQL('$stack.push()')],
                'Catch': [
                    {
                        'As': 'e',
                        'Do': [
                            YAQL("$reporter.report_error($this, $e.message)"),
                            {'Rethrow': None}
                        ]
                    }
                ],
                'Else': [
                    {YAQL('$.templateOutputs'): YAQL('$stack.output()')},
                    YAQL("$reporter.report($this, "
                         "'Stack was successfully created')"),

                    YAQL("$reporter.report($this, "
                         "'Application deployment has finished')"),
                ]
            }
        ]

        destroy = [
            {YAQL('$environment'): YAQL(
                "$.find('io.murano.Environment').require()"
            )},
            {YAQL('$stack'): YAQL(
                "new('io.murano.system.HeatStack', $environment, "
                "name => $.getAttr(generatedHeatStackName))")},
            YAQL('$stack.delete()')
        ]

        return {
            'Methods': {
                'deploy': {
                    'Body': deploy
                },
                'destroy': {
                    'Body': destroy
                }
            }
        }

    @staticmethod
    def _translate_ui_parameters(hot, title):
        groups = hot.get('parameter_groups', [])
        result_groups = []

        predefined_fields = [
            {
                'name': 'title',
                'type': 'string',
                'required': False,
                'hidden': True,
                'description': title
            },
            {
                'name': 'name',
                'type': 'string',
                'label': 'Application Name',
                'required': True,
                'description':
                    'Enter a desired name for the application.'
                    ' Just A-Z, a-z, 0-9, and dash are allowed'
            }
        ]
        used_parameters = set()
        hot_parameters = hot.get('parameters') or {}
        for group in groups:
            fields = []
            properties = []
            for parameter in group.get('parameters', []):
                parameter_value = hot_parameters.get(parameter)
                if parameter_value:
                    fields.append(HotPackage._translate_ui_parameter(
                        parameter, parameter_value))
                    used_parameters.add(parameter)
                    properties.append(parameter)
            result_groups.append((fields, properties))

        rest_group = []
        properties = []
        for key, value in hot_parameters.items():
            if key not in used_parameters:
                rest_group.append(HotPackage._translate_ui_parameter(
                    key, value))
                properties.append(key)
        if rest_group:
            result_groups.append((rest_group, properties))

        result_groups.insert(0, (predefined_fields, ['name']))
        return result_groups

    @staticmethod
    def _translate_ui_parameter(name, parameter_spec):
        translated = {
            'name': name,
            'label': name.title().replace('_', ' ')
        }
        parameter_type = parameter_spec['type']
        if parameter_type == 'number':
            translated['type'] = 'integer'
        elif parameter_type == 'boolean':
            translated['type'] = 'boolean'
        else:
            # string, json, and comma_delimited_list parameters are all
            # displayed as strings in UI. Any unsupported parameter would also
            # be displayed as strings.
            translated['type'] = 'string'

        label = parameter_spec.get('label')
        if label:
            translated['label'] = label

        if 'description' in parameter_spec:
            translated['description'] = parameter_spec['description']

        if 'default' in parameter_spec:
            translated['initial'] = parameter_spec['default']
            translated['required'] = False
        else:
            translated['required'] = True

        constraints = parameter_spec.get('constraints') or []
        translated_constraints = []

        for constraint in constraints:
            if 'length' in constraint:
                spec = constraint['length']
                if 'min' in spec:
                    translated['minLength'] = max(
                        translated.get('minLength', -sys.maxsize - 1),
                        int(spec['min']))
                if 'max' in spec:
                    translated['maxLength'] = min(
                        translated.get('maxLength', sys.maxsize),
                        int(spec['max']))

            elif 'range' in constraint:
                spec = constraint['range']
                if 'min' in spec and 'max' in spec:
                    ui_constraint = {
                        'expr': YAQL('$ >= {0} and $ <= {1}'.format(
                            spec['min'], spec['max']))
                    }
                elif 'min' in spec:
                    ui_constraint = {
                        'expr': YAQL('$ >= {0}'.format(spec['min']))
                    }
                else:
                    ui_constraint = {
                        'expr': YAQL('$ <= {0}'.format(spec['max']))
                    }
                if 'description' in constraint:
                    ui_constraint['message'] = constraint['description']
                translated_constraints.append(ui_constraint)

            elif 'allowed_values' in constraint:
                values = constraint['allowed_values']
                ui_constraint = {
                    'expr': YAQL('$ in list({0})'.format(', '.join(
                        [HotPackage._format_value(v) for v in values])))
                }
                if 'description' in constraint:
                    ui_constraint['message'] = constraint['description']
                translated_constraints.append(ui_constraint)

            elif 'allowed_pattern' in constraint:
                pattern = constraint['allowed_pattern']
                ui_constraint = {
                    'expr': {
                        'regexpValidator': pattern
                    }
                }
                if 'description' in constraint:
                    ui_constraint['message'] = constraint['description']
                translated_constraints.append(ui_constraint)

        if translated_constraints:
            translated['validators'] = translated_constraints

        return translated

    @staticmethod
    def _generate_application_ui(groups, type_name,
                                 package_name=None, package_version=None):
        app = {
            '?': {
                'type': type_name
            }
        }
        if package_name:
            app['?']['package'] = package_name
        if package_version:
            app['?']['classVersion'] = package_version
        for i, record in enumerate(groups):
            if i == 0:
                section = app
            else:
                section = app.setdefault('templateParameters', {})
            for property_name in record[1]:
                section[property_name] = YAQL(
                    '$.group{0}.{1}'.format(i, property_name))
        app['name'] = YAQL('$.group0.name')

        return app

    def _translate_ui(self):
        template_file = path.secure_join(
            self._source_directory, 'template.yaml')

        if not os.path.isfile(template_file):
            raise exceptions.PackageClassLoadError(
                self.full_name, 'File with class definition not found')
        with open(template_file) as stream:
            hot = yaml.safe_load(stream)

        groups = HotPackage._translate_ui_parameters(hot, self.description)
        forms = []
        for i, record in enumerate(groups):
            forms.append({'group{0}'.format(i): {'fields': record[0]}})

        translated = {
            'Version': 2,
            'Application': HotPackage._generate_application_ui(
                groups, self.full_name, self.full_name, str(self.version)),
            'Forms': forms
        }

        # see comment above about default_style
        return yaml.dump(translated, Dumper=Dumper, default_style='"')
