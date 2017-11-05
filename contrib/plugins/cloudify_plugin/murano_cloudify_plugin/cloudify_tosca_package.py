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

import yaml

from murano.common.helpers import path
from murano.packages import exceptions
from murano.packages import package_base

RESOURCES_DIR_NAME = 'Resources/'


class YAQL(object):
    def __init__(self, expr):
        self.expr = expr


class Dumper(yaml.SafeDumper):
    pass


def yaql_representer(dumper, data):
    return dumper.represent_scalar(u'!yaql', data.expr)


Dumper.add_representer(YAQL, yaql_representer)


class CloudifyToscaPackage(package_base.PackageBase):
    def __init__(self, format_name, runtime_version, source_directory,
                 manifest):
        super(CloudifyToscaPackage, self).__init__(
            format_name, runtime_version, source_directory, manifest)

        self._entry_point = manifest.get('EntryPoint', 'main.yaml')
        self._generated_class = None
        self._generated_ui = None

    @property
    def classes(self):
        return self.full_name,

    @property
    def requirements(self):
        return {
            'org.getcloudify.murano': '0'
        }

    @property
    def ui(self):
        if not self._generated_ui:
            self._generated_ui = self._generate_ui()
        return self._generated_ui

    def get_class(self, name):
        if name != self.full_name:
            raise exceptions.PackageClassLoadError(
                name, 'Class not defined in this package')
        if not self._generated_class:
            self._generated_class = self._generate_class()
        return self._generated_class, '<generated code>'

    def _generate_class(self):
        inputs, outputs = self._get_inputs_outputs()
        class_code = {
            'Name': self.full_name,
            'Extends': 'org.getcloudify.murano.CloudifyApplication',
            'Properties': self._generate_properties(inputs, outputs),
            'Methods': {
                'describe': self._generate_describe_method(inputs),
                'updateOutputs': self._generate_update_outputs_method(outputs)
            }
        }
        return yaml.dump(class_code, Dumper=Dumper, default_style='"')

    @staticmethod
    def _generate_properties(inputs, outputs):
        contracts = {}
        for name, value in inputs.items():
            prop = {
                'Contract': YAQL('$.string().notNull()'),
                'Usage': 'In'
            }
            if 'default' in value:
                prop['Default'] = value['default']
            contracts[name] = prop

        for name in outputs.keys():
            contracts[name] = {
                'Contract': YAQL('$.string()'),
                'Usage': 'Out'
            }

        return contracts

    def _generate_describe_method(self, inputs):
        input_values = {
            name: YAQL('$.' + name)
            for name in inputs.keys()
        }

        return {
            'Body': [{
                'Return': {
                    'entryPoint': self._entry_point,
                    'inputs': input_values
                }
            }]
        }

    @staticmethod
    def _generate_update_outputs_method(outputs):
        assignments = [
            {YAQL('$.' + name): YAQL('$outputs.get({0})'.format(name))}
            for name in outputs.keys()
        ]
        return {
            'Arguments': [{
                'outputs': {
                    'Contract': {
                        YAQL('$.string().notNull()'): YAQL('$')
                    }
                }
            }],
            'Body': assignments
        }

    def _get_inputs_outputs(self):
        entry_point_path = path.secure_join(
            self.source_directory, RESOURCES_DIR_NAME, self._entry_point)
        with open(entry_point_path) as blueprint:
            data = yaml.safe_load(blueprint)
            return data.get('inputs') or {}, data.get('outputs') or {}

    def _generate_application_ui_section(self, inputs, package_name=None,
                                         package_version=None):
        section = {
            key: YAQL(
                '$.appConfiguration.' + key) for key in inputs.keys()
        }
        section.update({
            '?': {
                'type': self.full_name
            }
        })
        if package_name:
            section['?']['package'] = package_name
        if package_version:
            section['?']['classVersion'] = package_version
        return section

    @staticmethod
    def _generate_form_ui_section(inputs):
        fields = [
            {
                'name': key,
                'label': key.title().replace('_', ' '),
                'type': 'string',
                'required': True,
                'description': value.get('description', key)
            } for key, value in inputs.items()
        ]
        return [{
            'appConfiguration': {
                'fields': fields
            }
        }]

    def _generate_ui(self):
        inputs, outputs = self._get_inputs_outputs()
        ui = {
            'Version': '2.2',
            'Application': self._generate_application_ui_section(
                inputs, self.full_name, str(self.version)),
            'Forms': self._generate_form_ui_section(inputs)
        }
        return yaml.dump(ui, Dumper=Dumper, default_style='"')
