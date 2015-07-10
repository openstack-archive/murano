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
import types

import yaml

from murano.dsl import yaql_expression
import murano.packages.application_package
from murano.packages import exceptions


YAQL = yaql_expression.YaqlExpression


class Dumper(yaml.Dumper):
    pass


def yaql_representer(dumper, data):
    return dumper.represent_scalar(u'!yaql', str(data))

Dumper.add_representer(YAQL, yaql_representer)


class HotPackage(murano.packages.application_package.ApplicationPackage):
    def __init__(self, source_directory, manifest, loader):
        super(HotPackage, self).__init__(source_directory, manifest, loader)
        self._translated_class = None
        self._source_directory = source_directory
        self._translated_ui = None

    @property
    def classes(self):
        return self.full_name,

    @property
    def ui(self):
        if not self._translated_ui:
            self._translated_ui = self._translate_ui()
        return self._translated_ui

    @property
    def raw_ui(self):
        ui_obj = self.ui
        result = yaml.dump(ui_obj, Dumper=Dumper, default_style='"')
        return result

    def get_class(self, name):
        if name != self.full_name:
            raise exceptions.PackageClassLoadError(
                name, 'Class not defined in this package')
        if not self._translated_class:
            self._translate_class()
        return self._translated_class

    def validate(self):
        self.get_class(self.full_name)
        if not self._translated_ui:
            self._translated_ui = self._translate_ui()
        super(HotPackage, self).validate()

    def _translate_class(self):
        template_file = os.path.join(self._source_directory, 'template.yaml')
        shutil.copy(template_file, self.get_resource(self.full_name))

        if not os.path.isfile(template_file):
            raise exceptions.PackageClassLoadError(
                self.full_name, 'File with class definition not found')
        with open(template_file) as stream:
            hot = yaml.safe_load(stream)
            if 'resources' not in hot:
                raise exceptions.PackageFormatError('Not a HOT template')
        translated = {
            'Name': self.full_name,
            'Extends': 'io.murano.Application'
        }

        parameters = HotPackage._translate_parameters(hot)
        parameters.update(HotPackage._translate_outputs(hot))
        translated['Properties'] = parameters

        translated.update(HotPackage._generate_workflow(hot))
        self._translated_class = translated

    @staticmethod
    def _translate_parameters(hot):
        result = {
            'generatedHeatStackName': {
                'Contract': YAQL('$.string()'),
                'Usage': 'Out'
            }
        }
        for key, value in (hot.get('parameters') or {}).items():
            result[key] = HotPackage._translate_parameter(value)
        result['name'] = {'Usage': 'In',
                          'Contract': YAQL('$.string().notNull()')}
        return result

    @staticmethod
    def _translate_parameter(value):
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

        result = {
            'Contract': YAQL(contract),
            "Usage": "In"
        }
        if 'default' in value:
            result['Default'] = value['default']
        return result

    @staticmethod
    def _translate_outputs(hot):
        result = {}
        for key, value in (hot.get('outputs') or {}).items():
            result[key] = {
                "Contract": YAQL("$.string()"),
                "Usage": "Out"
            }
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
        if isinstance(value, types.StringTypes):
            return str("'" + value + "'")
        return str(value)

    @staticmethod
    def _generate_workflow(hot):
        template_parameters = {}
        for key, value in (hot.get('parameters') or {}).items():
            template_parameters[key] = YAQL("$." + key)

        copy_outputs = []
        for key, value in (hot.get('outputs') or {}).items():
            copy_outputs.append({YAQL('$.' + key): YAQL('$outputs.' + key)})

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
                    YAQL('$.setAttr(generatedHeatStackName, randomName())')
                ]
            },
            {YAQL('$stack'): YAQL(
                "new('io.murano.system.HeatStack', "
                "name => $.getAttr(generatedHeatStackName))")},


            YAQL("$reporter.report($this, "
                 "'Application deployment has started')"),

            {YAQL('$resources'): YAQL("new('io.murano.system.Resources')")},
            {YAQL('$template'): YAQL("$resources.yaml(type($this))")},
            {YAQL('$parameters'): template_parameters},
            YAQL('$stack.setTemplate($template)'),
            YAQL('$stack.setParameters($parameters)'),

            YAQL("$reporter.report($this, "
                 "'Stack creation has started')"),
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
                    {YAQL('$outputs'): YAQL('$stack.output()')},
                    {'Do': copy_outputs},
                    YAQL("$reporter.report($this, "
                         "'Stack was successfully created')"),

                    YAQL("$reporter.report($this, "
                         "'Application deployment has finished')"),
                ]
            }
        ]

        destroy = [
            {YAQL('$stack'): YAQL(
                "new('io.murano.system.HeatStack', "
                "name => $.getAttr(generatedHeatStackName))")},
            YAQL('$stack.delete()')
        ]

        return {
            'Workflow': {
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
        result = [
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
        for key, value in (hot.get('parameters') or {}).items():
            result.append(HotPackage._translate_ui_parameter(key, value))
        return result

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
            # displayed as strings in UI. Any unsuported parameter would also
            # be displayed as strings.
            translated['type'] = 'string'

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
                        translated.get('minLength', -sys.maxint - 1),
                        int(spec['min']))
                if 'max' in spec:
                    translated['maxLength'] = min(
                        translated.get('maxLength', sys.maxint),
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
    def _generate_application_ui(hot, type_name):
        app = {
            '?': {
                'type': type_name
            }
        }
        for key in (hot.get('parameters') or {}).keys():
            app[key] = YAQL('$.appConfiguration.' + key)
        app['name'] = YAQL('$.appConfiguration.name')

        return app

    def _translate_ui(self):
        template_file = os.path.join(self._source_directory, 'template.yaml')

        if not os.path.isfile(template_file):
            raise exceptions.PackageClassLoadError(
                self.full_name, 'File with class definition not found')
        with open(template_file) as stream:
            hot = yaml.safe_load(stream)

        translated = {
            'Version': 2,
            'Application': HotPackage._generate_application_ui(
                hot, self.full_name),
            'Forms': [
                {
                    'appConfiguration': {
                        'fields': HotPackage._translate_ui_parameters(
                            hot, self.description)
                    }
                }
            ]
        }
        return translated
