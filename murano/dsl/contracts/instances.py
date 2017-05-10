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

from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes

from murano.dsl import constants
from murano.dsl import contracts
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import serializer


class Class(contracts.ContractMethod):
    name = 'class'

    @specs.parameter('name', dsl.MuranoTypeParameter(
        nullable=False, lazy=True))
    @specs.parameter('default_name', dsl.MuranoTypeParameter(
        nullable=True, lazy=True))
    @specs.parameter('version_spec', yaqltypes.String(True))
    def __init__(self, name, default_name=None, version_spec=None):
        self.type = name(self.context).type
        self.default_type = default_name(self.context) or self.type
        self.version_spec = version_spec

    def validate(self):
        if self.value is None or helpers.is_instance_of(
                self.value, self.type.name,
                self.version_spec or helpers.get_names_scope(
                    self.root_context)):
            return self.value
        if not isinstance(self.value, (dsl_types.MuranoObject,
                                       dsl_types.MuranoObjectInterface)):
            raise exceptions.ContractViolationException(
                'Value is not an object')
        raise exceptions.ContractViolationException(
            'Object of type {0} is not compatible with '
            'requested type {1}'.format(self.value.type, self.type))

    def transform(self):
        value = self.value
        object_store = helpers.get_object_store()
        if isinstance(self.value, contracts.ObjRef):
            value = self.value.object_id
        if value is None:
            return None
        if isinstance(value, dsl_types.MuranoObject):
            obj = value
        elif isinstance(value, dsl_types.MuranoObjectInterface):
            obj = value.object
        elif isinstance(value, utils.MappingType):
            obj = object_store.load(
                value, self.owner, context=self.root_context,
                default_type=self.default_type,
                scope_type=self.calling_type)
        elif isinstance(value, six.string_types):
            obj = object_store.get(value)
            if obj is None:
                if not object_store.initializing:
                    raise exceptions.NoObjectFoundError(value)
                else:
                    return contracts.ObjRef(value)
        else:
            raise exceptions.ContractViolationException(
                'Value {0} cannot be represented as class {1}'.format(
                    helpers.format_scalar(value), self.type))
        self.value = obj
        return self.validate()

    def generate_schema(self):
        return self.generate_class_schema(self.value, self.type)

    @staticmethod
    def generate_class_schema(value, type_):
        types = 'muranoObject'
        if '_notNull' not in value:
            types = [types] + ['null']

        return {
            'type': types,
            'muranoType': type_.name
        }


class Template(contracts.ContractMethod):
    name = 'template'

    @specs.parameter('type_', dsl.MuranoTypeParameter(
        nullable=False, lazy=True))
    @specs.parameter('default_type', dsl.MuranoTypeParameter(
        nullable=True, lazy=True))
    @specs.parameter('version_spec', yaqltypes.String(True))
    @specs.parameter(
        'exclude_properties', yaqltypes.Sequence(nullable=True))
    def __init__(self, engine, type_, default_type=None, version_spec=None,
                 exclude_properties=None):
        self.type = type_(self.context).type
        self.default_type = default_type(self.context) or self.type
        self.version_spec = version_spec
        self.exclude_properties = exclude_properties
        self.engine = engine

    def validate(self):
        if self.value is None or helpers.is_instance_of(
                self.value, self.type.name,
                self.version_spec or helpers.get_names_scope(
                    self.root_context)):
            return self.value
        if not isinstance(self.value, (dsl_types.MuranoObject,
                                       dsl_types.MuranoObjectInterface)):
            raise exceptions.ContractViolationException(
                'Value is not an object')
        raise exceptions.ContractViolationException(
            'Object of type {0} is not compatible with '
            'requested type {1}'.format(self.value.type, self.type))

    def check_type(self):
        if isinstance(self.value, utils.MappingType):
            return self.value
        return self.validate()

    def transform(self):
        object_store = helpers.get_object_store()
        if self.value is None:
            return None
        if isinstance(self.value, dsl_types.MuranoObject):
            obj = self.value
        elif isinstance(self.value, dsl_types.MuranoObjectInterface):
            obj = self.value.object
        elif isinstance(self.value, utils.MappingType):
            passkey = utils.create_marker('<Contract Passkey>')
            if self.exclude_properties:
                parsed = helpers.parse_object_definition(
                    self.value, self.calling_type, self.context)
                props = dsl.to_mutable(parsed['properties'], self.engine)
                for p in self.exclude_properties:
                    helpers.patch_dict(props, p, passkey)
                parsed['properties'] = props
                value = helpers.assemble_object_definition(parsed)
            else:
                value = self.value
            with helpers.thread_local_attribute(
                    constants.TL_CONTRACT_PASSKEY, passkey):
                with helpers.thread_local_attribute(
                        constants.TL_OBJECTS_DRY_RUN, True):
                    obj = object_store.load(
                        value, self.owner, context=self.context,
                        default_type=self.default_type,
                        scope_type=self.calling_type)
                    obj.__passkey__ = passkey
        else:
            raise exceptions.ContractViolationException(
                'Value {0} cannot be represented as class {1}'.format(
                    helpers.format_scalar(self.value), self.type))
        self.value = obj
        return self.validate()

    def finalize(self):
        if self.value is None:
            return None
        object_store = helpers.get_object_store()
        if object_store.initializing:
            return {}
        passkey = getattr(self.value, '__passkey__', None)
        with helpers.thread_local_attribute(
                constants.TL_CONTRACT_PASSKEY, passkey):
            result = serializer.serialize(
                self.value.real_this, object_store.executor,
                dsl_types.DumpTypes.Mixed)
            if self.exclude_properties:
                for p in self.exclude_properties:
                    helpers.patch_dict(result, p, utils.NO_VALUE)
            return result

    def generate_schema(self):
        result = Class.generate_class_schema(self.value, self.type)
        result['owned'] = True
        if self.exclude_properties:
            result['excludedProperties'] = self.exclude_properties
        return result


class Owned(contracts.ContractMethod):
    name = 'owned'

    def validate(self):
        if self.value is None or isinstance(self.value, contracts.ObjRef):
            return self.value
        if isinstance(self.value, dsl_types.MuranoObject):
            if helpers.find_object_owner(self.value, lambda t: t is self.this):
                return self.value
            raise exceptions.ContractViolationException(
                'Object {0} violates owned() contract'.format(self.value))
        raise exceptions.ContractViolationException(
            'Value {0} is not an object'.format(self.value))

    def transform(self):
        return self.validate()

    def generate_schema(self):
        self.value['owned'] = True
        return self.value


class NotOwned(contracts.ContractMethod):
    name = 'not_owned'

    def validate(self):
        if self.value is None or isinstance(self.value, contracts.ObjRef):
            return self.value
        if isinstance(self.value, dsl_types.MuranoObject):
            if helpers.find_object_owner(self.value, lambda t: t is self.this):
                raise exceptions.ContractViolationException(
                    'Object {0} violates notOwned() contract'.format(
                        self.value))
            return self.value
        raise exceptions.ContractViolationException(
            'Value {0} is not an object'.format(self.value))

    def transform(self):
        return self.validate()

    def generate_schema(self):
        self.value['owned'] = False
        return self.value
