# Copyright (c) 2016 Mirantis Inc.
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

import six
from yaql.language import exceptions as yaql_exceptions
from yaql.language import expressions
from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes

from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import executor
from murano.dsl import helpers
from murano.dsl import meta as meta_module
from murano.dsl import murano_type


def generate_schema(pkg_loader, context_manager,
                    class_name, method_names=None,
                    class_version=None, package_name=None):
    """Generate JSON schema

    JSON Schema is generated either for the class with all model builders
    or for specified model builders only. The return value is a dictionary
    with keys being model builder names and the values are JSON schemas for
    them. The class itself is represented by an empty string key.
    """

    if method_names and not isinstance(method_names, (list, tuple)):
        method_names = (method_names,)
    version = helpers.parse_version_spec(class_version)
    if package_name:
        package = pkg_loader.load_package(package_name, version)
    else:
        package = pkg_loader.load_class_package(class_name, version)

    cls = package.find_class(class_name, search_requirements=False)
    exc = executor.MuranoDslExecutor(pkg_loader, context_manager)
    with helpers.with_object_store(exc.object_store):
        context = prepare_context(exc, cls)
        model_builders = set(list_model_builders(cls, context))
        method_names = model_builders.intersection(
            method_names or model_builders)

        result = {
            name: generate_entity_schema(
                get_entity(cls, name), context, cls,
                get_meta(cls, name, context))
            for name in method_names
        }
        return result


def list_model_builders(cls, context):
    """List model builder names of the class

    Yield names of all model builders (static actions marked with appropriate
    metadata) plus empty string for the class itself.
    """

    yield ''
    for method_name in cls.all_method_names:
        try:
            method = cls.find_single_method(method_name)
            if not method.is_action or not method.is_static:
                continue
            meta = meta_module.aggregate_meta(method, context)
            is_builder = meta.get('io.murano.metadata.ModelBuilder')
            if is_builder and is_builder.get_property('enabled'):
                yield method.name
        except Exception:
            pass


def get_meta(cls, method_name, context):
    """Get metadata dictionary for the method or class"""
    if not method_name:
        return meta_module.aggregate_meta(cls, context)

    method = cls.find_single_method(method_name)
    return meta_module.aggregate_meta(method, context)


def get_entity(cls, method_name):
    """Get MuranoMethod of the class by its name"""
    if not method_name:
        return cls
    method = cls.find_single_method(method_name)
    return method


def get_properties(entity):
    """Get properties/arg scheme of the class/method"""
    if isinstance(entity, dsl_types.MuranoType):
        properties = entity.all_property_names
        result = {}
        for prop_name in properties:
            prop = entity.find_single_property(prop_name)

            if prop.usage not in (dsl_types.PropertyUsages.In,
                                  dsl_types.PropertyUsages.InOut):
                continue
            result[prop_name] = prop
        return result
    return entity.arguments_scheme


def prepare_context(exc, cls):
    """Registers alternative implementations of contract YAQL functions"""
    context = exc.create_object_context(cls).create_child_context()
    context[constants.CTX_NAMES_SCOPE] = cls
    context.register_function(string_)
    context.register_function(int_)
    context.register_function(bool_)
    context.register_function(not_null)
    context.register_function(check)
    context.register_function(class_factory(context))
    context.register_function(owned)
    context.register_function(not_owned)
    context.register_function(finalize)
    return context


def generate_entity_schema(entity, context, declaring_type, meta):
    """Generate schema for single class or method by it DSL entity"""
    properties = get_properties(entity)
    type_weights = murano_type.weigh_type_hierarchy(declaring_type)
    schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'properties': {
            name: generate_property_schema(prop, context, type_weights)
            for name, prop in six.iteritems(properties)
            },
        'additionalProperties': False,
        'formSections': generate_sections(meta, type_weights)
    }
    schema.update(generate_ui_hints(entity, context, type_weights))
    return schema


def generate_sections(meta, type_weights):
    """Builds sections definitions for the schema

    Sections are UI hint for UI for grouping inputs into tabs/group-boxes.
    The code collects section definitions from type hierarchy considering that
    the section might be redefined in ancestor with the different section
    index and then re-enumerates them in a way that sections from the most
    base classes in hierarchy will get lower index values and there be no
    two sections with the same index.
    """
    section_list = meta.get('io.murano.metadata.forms.Section', [])
    sections_map = {}
    for section in section_list:
        name = section.get_property('name')
        ex_section = sections_map.get(name)
        if not ex_section:
            pass
        elif (type_weights[ex_section.declaring_type.name] <
                type_weights[section.declaring_type.name]):
            continue
        elif (type_weights[ex_section.declaring_type.name] ==
                type_weights[section.declaring_type.name]):
            index = section.get_property('index')
            if index is None:
                continue
            ex_index = ex_section.get_property('index')
            if ex_index is not None and ex_index <= index:
                continue
        sections_map[name] = section

    ordered_sections, unordered_sections = sort_by_index(
        sections_map.values(), type_weights)
    sections = {}
    index = 0
    for section in ordered_sections:
        name = section.get_property('name')
        if name not in sections:
            sections[name] = {
                'title': section.get_property('title'),
                'index': index
            }
            index += 1
    for section in unordered_sections:
        name = section.get_property('name')
        if name not in sections:
            sections[name] = {
                'title': section.get_property('title')
            }
    return sections


def generate_property_schema(prop, context, type_weights):
    """Generate schema for single property/argument"""
    schema = translate(prop.contract.spec, context)
    if prop.has_default:
        schema['default'] = prop.default
    schema.update(generate_ui_hints(prop, context, type_weights))
    return schema


def generate_ui_hints(entity, context, type_weights):
    """Translate know property/arg meta into json-schema UI hints"""
    schema = {}
    meta = meta_module.aggregate_meta(entity, context)
    for cls_name, schema_prop, meta_prop in (
            ('io.murano.metadata.Title', 'title', 'text'),
            ('io.murano.metadata.Description', 'description', 'text'),
            ('io.murano.metadata.HelpText', 'helpText', 'text'),
            ('io.murano.metadata.forms.Hidden', 'visible', 'visible')):
        value = meta.get(cls_name)
        if value is not None:
            schema[schema_prop] = value.get_property(meta_prop)

    position = meta.get('io.murano.metadata.forms.Position')
    if position:
        schema['formSection'] = position.get_property('section')
        index = position.get_property('index')
        if index is not None:
            schema['formIndex'] = (
                (position.get_property('index') + 1) * len(type_weights) -
                type_weights[position.declaring_type.name])

    return schema


def sort_by_index(meta, type_weights, property_name='index'):
    """Sorts meta definitions by its distance in the class hierarchy"""
    has_index = six.moves.filter(
        lambda m: m.get_property(property_name) is not None, meta)
    has_no_index = six.moves.filter(
        lambda m: m.get_property(property_name) is None, meta)

    return (
        sorted(has_index,
               key=lambda m: (
                   (m.get_property(property_name) + 1) *
                   len(type_weights) -
                   type_weights[m.declaring_type.name])),
        has_no_index)


class Schema(object):
    """Container object to define YAQL contracts on"""
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return repr(self.data)


@specs.parameter('schema', Schema)
@specs.method
def string_(schema):
    """Implementation of string() contract that generates schema instead"""
    types = 'string'
    if '_notNull' not in schema.data:
        types = [types] + ['null']

    return Schema({
        'type': types
    })


def class_factory(context):
    """Factory for class() contract function that generates schema instead"""
    @specs.parameter('schema', Schema)
    @specs.parameter('name', dsl.MuranoTypeParameter(
        nullable=False, context=context))
    @specs.parameter('default_name', dsl.MuranoTypeParameter(
        nullable=True, context=context))
    @specs.parameter('version_spec', yaqltypes.String(True))
    @specs.method
    def class_(schema, name, default_name=None, version_spec=None):
        types = 'muranoObject'
        if '_notNull' not in schema.data:
            types = [types] + ['null']

        return Schema({
            'type': types,
            'muranoType': name.type.name
        })

    return class_


@specs.parameter('schema', Schema)
@specs.method
def not_owned(schema):
    """Implementation of notOwned() contract that generates schema instead"""
    schema.data['owned'] = False
    return schema


@specs.parameter('schema', Schema)
@specs.method
def owned(schema):
    """Implementation of owned() contract that generates schema instead"""
    schema.data['owned'] = True
    return schema


@specs.parameter('schema', Schema)
@specs.method
def int_(schema):
    """Implementation of int() contract that generates schema instead"""
    types = 'integer'
    if '_notNull' not in schema.data:
        types = [types] + ['null']

    return Schema({
        'type': types
    })


@specs.parameter('schema', Schema)
@specs.method
def bool_(schema):
    """Implementation of bool() contract that generates schema instead"""
    types = 'boolean'
    if '_notNull' not in schema.data:
        types = [types] + ['null']

    return Schema({
        'type': types
    })


@specs.parameter('schema', Schema)
@specs.method
def not_null(schema):
    """Implementation of notNull() contract that generates schema instead"""
    types = schema.data.get('type')
    if isinstance(types, list) and 'null' in types:
        types.remove('null')
        if len(types) == 1:
            types = types[0]
        schema.data['type'] = types
    schema.data['_notNull'] = True
    return schema


@specs.inject('up', yaqltypes.Super())
@specs.name('#finalize')
def finalize(obj, up):
    """Wrapper around YAQL contracts that removes temporary schema data"""
    res = up(obj)
    if isinstance(res, Schema):
        res = res.data
    if isinstance(res, dict):
        res.pop('_notNull', None)
    return res


@specs.parameter('expr', yaqltypes.YaqlExpression())
@specs.parameter('schema', Schema)
@specs.method
def check(schema, expr, engine, context):
    """Implementation of check() contract that generates schema instead"""
    rest = [True]
    while rest:
        if (isinstance(expr, expressions.BinaryOperator) and
                expr.operator == 'and'):
            rest = expr.args[1]
            expr = expr.args[0]
        else:
            rest = []
        res = extract_pattern(expr, engine, context)
        if res is not None:
            schema.data.update(res)
        expr = rest
    return schema


def extract_pattern(expr, engine, context):
    """Translation of certain known patterns of check() contract expressions"""
    if isinstance(expr, expressions.BinaryOperator):
        ops = ('>', '<', '>=', '<=')
        if expr.operator in ops:
            op_index = ops.index(expr.operator)
            if is_dollar(expr.args[0]):
                constant = evaluate_constant(expr.args[1], engine, context)
                if constant is None:
                    return None
            elif is_dollar(expr.args[1]):
                constant = evaluate_constant(expr.args[0], engine, context)
                if constant is None:
                    return None
                op_index = -1 - op_index
            else:
                return None
            op = ops[op_index]
            if op == '>':
                return {'minimum': constant, 'exclusiveMinimum': True}
            elif op == '>=':
                return {'minimum': constant, 'exclusiveMinimum': False}
            if op == '<':
                return {'maximum': constant, 'exclusiveMaximum': True}
            elif op == '<=':
                return {'maximum': constant, 'exclusiveMaximum': False}
        elif expr.operator == 'in' and is_dollar(expr.args[0]):
            lst = evaluate_constant(expr.args[1], engine, context)
            if isinstance(lst, tuple):
                return {'enum': list(lst)}

        elif (expr.operator == '.' and is_dollar(expr.args[0]) and
                isinstance(expr.args[1], expressions.Function)):
            func = expr.args[1]
            if func.name == 'matches':
                constant = evaluate_constant(func.args[0], engine, context)
                if constant is not None:
                    return {'pattern': constant}


def is_dollar(expr):
    """Check $-expressions in YAQL AST"""
    return (isinstance(expr, expressions.GetContextValue) and
            expr.path.value in ('$', '$1'))


def evaluate_constant(expr, engine, context):
    """Evaluate yaql expression into constant value if possible"""
    if isinstance(expr, expressions.Constant):
        return expr.value
    context = context.create_child_context()
    trap = utils.create_marker('trap')
    context['$'] = trap

    @specs.parameter('name', yaqltypes.StringConstant())
    @specs.name('#get_context_data')
    def get_context_data(name, context):
        res = context[name]
        if res is trap:
            raise yaql_exceptions.ResolutionError()
        return res

    context.register_function(get_context_data)

    try:
        return expressions.Statement(expr, engine).evaluate(context=context)
    except yaql_exceptions.YaqlException:
        return None


def translate(contract, context):
    """Translates contracts into json-schema equivalents"""
    if isinstance(contract, dict):
        return translate_dict(contract, context)
    elif isinstance(contract, list):
        return translate_list(contract, context)
    elif isinstance(contract, (dsl_types.YaqlExpression,
                               expressions.Statement)):
        context = context.create_child_context()
        context['$'] = Schema({})
        return contract(context=context)


def translate_dict(contract, context):
    """Translates dictionary contracts into json-schema objects"""
    properties = {}
    additional_properties = False
    for key, value in six.iteritems(contract):
        if isinstance(key, dsl_types.YaqlExpression):
            additional_properties = translate(value, context)
        else:
            properties[key] = translate(value, context)
    return {
        'type': 'object',
        'properties': properties,
        'additionalProperties': additional_properties
    }


def translate_list(contract, context):
    """Translates list contracts into json-schema arrays"""
    items = []
    for value in contract:
        if isinstance(value, int):
            pass
        else:
            items.append(translate(value, context))
    if len(items) == 0:
        return {'type': 'array'}
    elif len(items) == 1:
        return {
            'type': 'array',
            'items': items[0],
        }
    else:
        return {
            'type': 'array',
            'items': items,
            'additionalItems': items[-1]
        }
