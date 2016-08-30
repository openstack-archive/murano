#    Copyright (c) 2016 Mirantis, Inc.
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

import six

from murano.dsl import contracts
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers


class String(contracts.ContractMethod):
    name = 'string'

    def transform(self):
        if self.value is None:
            return None
        if isinstance(self.value, six.text_type):
            return self.value
        if isinstance(self.value, six.string_types) or \
                isinstance(self.value, six.integer_types):
            return six.text_type(self.value)
        if isinstance(self.value, dsl_types.MuranoObject):
            return self.value.object_id
        if isinstance(self.value, dsl_types.MuranoObjectInterface):
            return self.value.id
        raise exceptions.ContractViolationException(
            'Value {0} violates string() contract'.format(
                helpers.format_scalar(self.value)))

    def validate(self):
        if self.value is None or isinstance(self.value, six.string_types):
            return self.value
        raise exceptions.ContractViolationException()

    def generate_schema(self):
        types = 'string'
        if '_notNull' not in self.value:
            types = [types] + ['null']

        return {
            'type': types
        }


class Bool(contracts.ContractMethod):
    name = 'bool'

    def validate(self):
        if self.value is None or isinstance(self.value, bool):
            return self.value
        raise exceptions.ContractViolationException()

    def transform(self):
        if self.value is None:
            return None
        return True if self.value else False

    def generate_schema(self):
        types = 'boolean'
        if '_notNull' not in self.value:
            types = [types] + ['null']

        return {
            'type': types
        }


class Int(contracts.ContractMethod):
    name = 'int'

    def validate(self):
        if self.value is None or isinstance(
                self.value, int) and not isinstance(self.value, bool):
            return self.value
        raise exceptions.ContractViolationException()

    def transform(self):
        if self.value is None:
            return None
        try:
            return int(self.value)
        except Exception:
            raise exceptions.ContractViolationException(
                'Value {0} violates int() contract'.format(
                    helpers.format_scalar(self.value)))

    def generate_schema(self):
        types = 'integer'
        if '_notNull' not in self.value:
            types = [types] + ['null']

        return {
            'type': types
        }


class NotNull(contracts.ContractMethod):
    name = 'not_null'

    def validate(self):
        if self.value is None:
            raise exceptions.ContractViolationException(
                'null value violates notNull() contract')
        return self.value

    def transform(self):
        return self.validate()

    def generate_schema(self):
        types = self.value.get('type')
        if isinstance(types, list) and 'null' in types:
            types.remove('null')
            if len(types) == 1:
                types = types[0]
            self.value['type'] = types
        self.value['_notNull'] = True
        return self.value
