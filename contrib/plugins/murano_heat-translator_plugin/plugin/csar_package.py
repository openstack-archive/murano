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
import six
import sys
import yaml
import zipfile

from murano.packages import exceptions
from murano.packages import package_base
from toscaparser.common import exception as csar_exception
from toscaparser.prereq import csar
from toscaparser.tosca_template import ToscaTemplate
from translator.hot.tosca_translator import TOSCATranslator

CSAR_RESOURCES_DIR_NAME = 'Resources/'
CSAR_FILES_DIR_NAME = 'CSARFiles/'
CSAR_ENV_DIR_NAME = 'CSAREnvironments/'


class YAQL(object):
    def __init__(self, expr):
        self.expr = expr


class Dumper(yaml.SafeDumper):
    pass


def yaql_representer(dumper, data):
    return dumper.represent_scalar(u'!yaql', data.expr)


Dumper.add_representer(YAQL, yaql_representer)


class CSARPackage(package_base.PackageBase):
    def __init__(self, format_name, runtime_version, source_directory,
                 manifest):
        super(CSARPackage, self).__init__(
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
        csar_file = os.path.join(self._source_directory, 'csar.zip')
        shutil.copy(csar_file, self.get_resource(self.full_name))

        if not os.path.isfile(csar_file):
            raise exceptions.PackageClassLoadError(
                self.full_name, 'File with class definition not found')

        csar_obj = csar.CSAR(csar_file)
        try:
            csar_obj.validate()
        except csar_exception.ValidationError as ve:
            raise exceptions.PackageFormatError('Not a CSAR archive: ' +
                                                str(ve))

        translated = {
            'Name': self.full_name,
            'Extends': 'io.murano.Application'
        }

        csar_envs_path = os.path.join(self._source_directory,
                                      CSAR_RESOURCES_DIR_NAME,
                                      CSAR_ENV_DIR_NAME)

        validate_csar_parameters = (not os.path.isdir(csar_envs_path) or
                                    not os.listdir(csar_envs_path))

        tosca = csar_obj.get_main_template_yaml()
        parameters = CSARPackage._build_properties(tosca,
                                                   validate_csar_parameters)
        parameters.update(CSARPackage._translate_outputs(tosca))
        translated['Properties'] = parameters
        hot = yaml.load(self._translate('tosca', csar_obj.csar,
                                        parameters, True))
        files = CSARPackage._translate_files(self._source_directory)

        template_file = os.path.join(self._source_directory,
                                     CSAR_RESOURCES_DIR_NAME, 'template.yaml')
        with open(template_file, 'w') as outfile:
            outfile.write(yaml.safe_dump(hot))
        translated.update(CSARPackage._generate_workflow(hot, files))
        self._translated_class = yaml.dump(translated, Dumper=Dumper,
                                           default_style='"')

    def _translate(self, sourcetype, path, parsed_params, a_file):
        output = None
        if sourcetype == "tosca":
            tosca = ToscaTemplate(path, parsed_params, a_file)
            translator = TOSCATranslator(tosca, parsed_params)
            output = translator.translate()
        return output

    @staticmethod
    def _build_properties(csar, csar_parameters):
        result = {
            'generatedHeatStackName': {
                'Contract': YAQL('$.string()'),
                'Usage': 'Out'
            },
            'hotEnvironment': {
                'Contract': YAQL('$.string()'),
                'Usage': 'In'
            }
        }

        if csar_parameters:
            params_dict = {}
            for key, value in (csar.get('parameters') or {}).items():
                param_contract = \
                    CSARPackage._translate_param_to_contract(value)
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
        elif parameter_type == 'integer':
            contract += '.int()'
        elif parameter_type == 'boolean':
            contract += '.bool()'
        else:
            raise ValueError('Unsupported parameter type ' + parameter_type)

        constraints = value.get('constraints') or []
        for constraint in constraints:
            translated = CSARPackage._translate_constraint(constraint)
            if translated:
                contract += translated

        result = YAQL(contract)
        return result

    @staticmethod
    def _translate_outputs(csar):
        result = {}
        for key in (csar.get('outputs') or {}).keys():
            result[key] = {
                "Contract": YAQL("$.string()"),
                "Usage": "Out"
            }
        return result

    @staticmethod
    def _translate_files(source_directory):
        source = os.path.join(source_directory, 'csar.zip')
        dest_dir = os.path.join(source_directory, CSAR_RESOURCES_DIR_NAME,
                                CSAR_FILES_DIR_NAME)
        with zipfile.ZipFile(source, "r") as z:
            z.extractall(dest_dir)
        csar_files_path = os.path.join(source_directory,
                                       CSAR_RESOURCES_DIR_NAME,
                                       CSAR_FILES_DIR_NAME)
        return CSARPackage._build_csar_resources(csar_files_path)

    @staticmethod
    def _build_csar_resources(basedir):
        result = []
        if os.path.isdir(basedir):
            for root, _, files in os.walk(os.path.abspath(basedir)):
                for f in files:
                    full_path = os.path.join(root, f)
                    relative_path = os.path.relpath(full_path, basedir)
                    result.append(relative_path)
        return result

    @staticmethod
    def _translate_constraint(constraint):
        if 'equal' in constraint:
            return CSARPackage._translate_equal_constraint(
                constraint['equal'])
        elif 'valid_values' in constraint:
            return CSARPackage._translate_valid_values_constraint(
                constraint['valid_values'])
        elif 'length' in constraint:
            return CSARPackage._translate_length_constraint(
                constraint['length'])
        elif 'in_range' in constraint:
            return CSARPackage._translate_range_constraint(
                constraint['in_range'])
        elif 'allowed_pattern' in constraint:
            return CSARPackage._translate_allowed_pattern_constraint(
                constraint['allowed_pattern'])

    @staticmethod
    def _translate_equal_constraint(value):
        return ".check($ == {0})".format(value)

    @staticmethod
    def _translate_allowed_pattern_constraint(value):
        return ".check(matches($, '{0}'))".format(value)

    @staticmethod
    def _translate_valid_values_constraint(values):
        return '.check($ in list({0}))'.format(
            ', '.join([CSARPackage._format_value(v) for v in values]))

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
            return u"{}".format(value)
        return six.text_type(value)

    @staticmethod
    def _generate_workflow(csar, files):
        hot_files_map = {}
        for f in files:
            file_path = "$resources.string('{0}{1}')".format(
                CSAR_FILES_DIR_NAME, f)
            hot_files_map['../{0}'.format(f)] = YAQL(file_path)

        hot_env = YAQL("$.hotEnvironment")

        copy_outputs = []
        for key in (csar.get('outputs') or {}).keys():
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

            {YAQL('$template'): YAQL("$resources.yaml('template.yaml')")},
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
                        CSAR_ENV_DIR_NAME))},
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
            {YAQL('$environment'): YAQL(
                "$.find('io.murano.Environment').require()"
            )},
            {YAQL('$stack'): YAQL(
                "new('io.murano.system.HeatStack', $environment, "
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
    def _translate_ui_parameters(tosca, title):
        result_groups = []

        used_inputs = set()
        tosca_inputs = tosca.get('topology_template').get('inputs') or {}
        fields = []
        properties = []
        for input in tosca_inputs:
            input_value = tosca_inputs.get(input)
            if input_value:
                fields.append(CSARPackage._translate_ui_parameter(
                    input, input_value))
                used_inputs.add(input)
                properties.append(input)
        if fields or properties:
            result_groups.append((fields, properties))

        rest_group = []
        properties = []
        for key, value in tosca_inputs.items():
            if key not in used_inputs:
                rest_group.append(CSARPackage._translate_ui_parameter(
                    key, value))
                properties.append(key)
        if rest_group:
            result_groups.append((rest_group, properties))

        return result_groups

    @staticmethod
    def _translate_ui_parameter(name, parameter_spec):
        translated = {
            'name': name,
            'label': name.title().replace('_', ' ')
        }
        parameter_type = parameter_spec['type']
        if parameter_type == 'integer':
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

            elif 'valid_values' in constraint:
                values = constraint['valid_values']
                ui_constraint = {
                    'expr': YAQL('$ in list({0})'.format(', '.join(
                        [CSARPackage._format_value(v) for v in values])))
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
    def _generate_application_ui(groups, type_name, package_name=None,
                                 package_version=None):
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
            section = app.setdefault('templateParameters', {})

            for property_name in record[1]:
                section[property_name] = YAQL(
                    '$.group{0}.{1}'.format(i, property_name))

        return app

    def _translate_ui(self):
        tosca = csar.CSAR(os.path.join(self._source_directory, 'csar.zip'))\
            .get_main_template_yaml()

        groups = CSARPackage._translate_ui_parameters(tosca, self.description)
        forms = []
        for i, record in enumerate(groups):
            forms.append({'group{0}'.format(i): {'fields': record[0]}})

        translated = {
            'Version': 2.2,
            'Application': CSARPackage._generate_application_ui(
                groups, self.full_name, self.full_name, str(self.version)),
            'Forms': forms
        }
        return yaml.dump(translated, Dumper=Dumper, default_style='"')
