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

import semantic_version
from yaql.language import specs
from yaql import yaqlization

from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.dsl import meta


@specs.yaql_property(dsl_types.MuranoType)
@specs.name('name')
def type_name(murano_type):
    return murano_type.name


@specs.yaql_property(dsl_types.MuranoType)
@specs.name('usage')
def type_usage(murano_type):
    return murano_type.usage


@specs.yaql_property(dsl_types.MuranoClass)
def methods(murano_class):
    all_method_names = murano_class.all_method_names
    return tuple(
        murano_method
        for name in all_method_names
        if not name.startswith('__') and not name.startswith('.')
        for murano_method in murano_class.find_method(name)
    )


@specs.yaql_property(dsl_types.MuranoClass)
def properties(murano_class):
    all_property_names = murano_class.all_property_names
    return tuple(
        prop
        for prop_name in all_property_names
        if not prop_name.startswith('__') and not prop_name.startswith('.')
        for prop in murano_class.find_property(prop_name)
    )


@specs.yaql_property(dsl_types.MuranoClass)
def ancestors(murano_class):
    return tuple(murano_class.ancestors())


@specs.yaql_property(dsl_types.MuranoType)
def package(murano_type):
    return murano_type.package


@specs.yaql_property(dsl_types.MuranoClass)
@specs.name('version')
def type_version(murano_type):
    return murano_type.version


@specs.yaql_property(dsl_types.MuranoProperty)
@specs.name('name')
def property_name(murano_property):
    return murano_property.name


# TODO(ativelkov): add 'default' to return some wrapped YAQL expression
# @specs.yaql_property(dsl_types.MuranoProperty)
# @specs.name('default')
# def property_default(murano_property):
#     return murano_property.default


@specs.yaql_property(dsl_types.MuranoProperty)
@specs.name('has_default')
def property_has_default(murano_property):
    return murano_property.has_default


@specs.yaql_property(dsl_types.MuranoProperty)
@specs.name('usage')
def property_usage(murano_property):
    return murano_property.usage


@specs.yaql_property(dsl_types.MuranoProperty)
@specs.name('declaring_type')
def property_owner(murano_property):
    return murano_property.declaring_type


@specs.name('get_value')
@specs.parameter('property_', dsl_types.MuranoProperty)
@specs.parameter('object_', dsl.MuranoObjectParameter(
    nullable=True, decorate=False))
@specs.method
def property_get_value(context, property_, object_):
    if object_ is None:
        return helpers.get_executor().get_static_property(
            property_.declaring_type, name=property_.name, context=context)
    return object_.cast(property_.declaring_type).get_property(
        name=property_.name, context=context)


@specs.name('set_value')
@specs.parameter('property_', dsl_types.MuranoProperty)
@specs.parameter('object_', dsl.MuranoObjectParameter(
    nullable=True, decorate=False))
@specs.method
def property_set_value(context, property_, object_, value):
    if object_ is None:
        helpers.get_executor().set_static_property(
            property_.declaring_type,
            name=property_.name, value=value, context=context)
    else:
        object_.cast(property_.declaring_type).set_property(
            name=property_.name, value=value, context=context)


@specs.yaql_property(dsl_types.MuranoMethod)
@specs.name('name')
def method_name(murano_method):
    return murano_method.name


@specs.yaql_property(dsl_types.MuranoMethod)
def arguments(murano_method):
    if murano_method.arguments_scheme is None:
        return None
    return tuple(murano_method.arguments_scheme.values())


@specs.yaql_property(dsl_types.MuranoMethod)
@specs.name('declaring_type')
def method_owner(murano_method):
    return murano_method.declaring_type


@specs.parameter('method', dsl_types.MuranoMethod)
@specs.parameter('__object', dsl.MuranoObjectParameter(nullable=True))
@specs.name('invoke')
@specs.method
def method_invoke(context, method, __object, *args, **kwargs):
    return method.invoke(__object, args, kwargs, context)


@specs.yaql_property(dsl_types.MuranoPackage)
def types(murano_package):
    return tuple(
        murano_package.find_class(cls, False)
        for cls in murano_package.classes
    )


@specs.yaql_property(dsl_types.MuranoPackage)
@specs.name('name')
def package_name(murano_package):
    return murano_package.name


@specs.yaql_property(dsl_types.MuranoPackage)
@specs.name('version')
def package_version(murano_package):
    return murano_package.version


@specs.yaql_property(dsl_types.MuranoMethodArgument)
@specs.name('name')
def argument_name(method_argument):
    return method_argument.name

# TODO(ativelkov): add 'default' to return some wrapped YAQL expression
# @specs.yaql_property(dsl_types.MuranoMethodArgument)
# @specs.name('default')
# def argument_default(method_argument):
#     return method_argument.default


@specs.yaql_property(dsl_types.MuranoMethodArgument)
@specs.name('has_default')
def argument_has_default(method_argument):
    return method_argument.has_default


@specs.yaql_property(dsl_types.MuranoMethodArgument)
@specs.name('usage')
def argument_usage(method_argument):
    return method_argument.usage


@specs.yaql_property(dsl_types.MuranoMethodArgument)
@specs.name('declaring_method')
def argument_owner(method_argument):
    return method_argument.murano_method


@specs.yaql_property(dsl_types.MuranoType)
@specs.name('type')
def type_to_type_ref(murano_type):
    return murano_type.get_reference()


@specs.parameter('provider', meta.MetaProvider)
@specs.name('#property#meta')
def get_meta(context, provider):
        return provider.get_meta(context)


@specs.yaql_property(dsl_types.MuranoMetaClass)
def cardinality(murano_meta_class):
    return murano_meta_class.cardinality


@specs.yaql_property(dsl_types.MuranoMetaClass)
def targets(murano_meta_class):
    return murano_meta_class.targets


@specs.yaql_property(dsl_types.MuranoMetaClass)
def inherited(murano_meta_class):
    return murano_meta_class.inherited


def register(context):
    funcs = (
        type_name, type_usage, type_version, type_to_type_ref,
        methods, properties, ancestors, package,
        property_name, property_has_default, property_owner,
        property_usage, property_get_value, property_set_value,
        method_name, arguments, method_owner, method_invoke,
        types, package_name, package_version,
        argument_name, argument_has_default, argument_owner,
        argument_usage,
        cardinality, targets, inherited,
        get_meta
    )
    for f in funcs:
        context.register_function(f)

yaqlization.yaqlize(semantic_version.Version, whitelist=[
    'major', 'minor', 'patch', 'prerelease', 'build'
])
