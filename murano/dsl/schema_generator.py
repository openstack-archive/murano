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

from murano.dsl.contracts import contracts
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
        context = exc.create_object_context(cls)
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


def generate_entity_schema(entity, context, declaring_type, meta):
    """Generate schema for single class or method by it DSL entity"""
    properties = get_properties(entity)
    type_weights = murano_type.weigh_type_hierarchy(declaring_type)
    schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'type': 'object',
        'properties': {
            name: generate_property_schema(prop, context, type_weights)
            for name, prop in properties.items()
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
    schema = translate(prop.contract.spec, context,
                       prop.declaring_type.package.runtime_version)
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


def translate(contract, context, runtime_version):
    """Translates contracts into json-schema equivalents"""
    if isinstance(contract, dict):
        return translate_dict(contract, context, runtime_version)
    elif isinstance(contract, list):
        return translate_list(contract, context, runtime_version)
    elif isinstance(contract, dsl_types.YaqlExpression):
        return contracts.Contract.generate_expression_schema(
            contract, context, runtime_version)


def translate_dict(contract, context, runtime_version):
    """Translates dictionary contracts into json-schema objects"""
    properties = {}
    additional_properties = False
    for key, value in contract.items():
        if isinstance(key, dsl_types.YaqlExpression):
            additional_properties = translate(value, context, runtime_version)
        else:
            properties[key] = translate(value, context, runtime_version)
    return {
        'type': 'object',
        'properties': properties,
        'additionalProperties': additional_properties
    }


def translate_list(contract, context, runtime_version):
    """Translates list contracts into json-schema arrays"""
    items = []
    for value in contract:
        if isinstance(value, int):
            pass
        else:
            items.append(translate(value, context, runtime_version))
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
