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

import abc
import collections
import copy
import weakref

import semantic_version
import six
from yaql.language import utils

from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import meta as dslmeta
from murano.dsl import murano_method
from murano.dsl import murano_object
from murano.dsl import murano_property
from murano.dsl import yaql_integration


class MuranoType(dsl_types.MuranoType):
    def __init__(self, ns_resolver, name, package):
        self._namespace_resolver = ns_resolver
        self._name = name
        self._package = weakref.ref(package)

    @property
    def name(self):
        return self._name

    @property
    def package(self):
        return self._package()

    @property
    def namespace_resolver(self):
        return self._namespace_resolver

    @abc.abstractproperty
    def usage(self):
        raise NotImplementedError()

    @property
    def version(self):
        return self.package.version

    def get_reference(self):
        return dsl_types.MuranoTypeReference(self)


class MuranoClass(dsl_types.MuranoClass, MuranoType, dslmeta.MetaProvider):
    _allowed_usages = {dsl_types.ClassUsages.Class}

    def __init__(self, ns_resolver, name, package, parents, meta=None,
                 imports=None):
        super(MuranoClass, self).__init__(ns_resolver, name, package)
        self._methods = {}
        self._properties = {}
        self._config = {}
        self._extension_class = None
        if (self._name == constants.CORE_LIBRARY_OBJECT or
                parents is utils.NO_VALUE):
            self._parents = []
        else:
            self._parents = parents or [
                package.find_class(constants.CORE_LIBRARY_OBJECT)]
        for p in self._parents:
            if p.usage not in self._allowed_usages:
                raise exceptions.InvalidInheritanceError(
                    u'Type {0} cannot have parent with Usage {1}'.format(
                        self.name, p.usage))
        remappings = self._build_parent_remappings()
        self._parents = self._adjusted_parents(remappings)
        self._context = None
        self._exported_context = None
        self._meta = dslmeta.MetaData(meta, dsl_types.MetaTargets.Type, self)
        self._meta_values = None
        self._imports = list(self._resolve_imports(imports))

    def _adjusted_parents(self, remappings):
        seen = {}

        def altered_clone(class_):
            seen_class = seen.get(class_)
            if seen_class is not None:
                return seen_class

            cls_remapping = remappings.get(class_)

            if cls_remapping is not None:
                return altered_clone(cls_remapping)

            new_parents = [altered_clone(p) for p in class_._parents]
            if all(a is b for a, b in zip(class_._parents, new_parents)):
                return class_
            res = copy.copy(class_)
            res._parents = new_parents
            res._meta_values = None
            res._context = None
            res._exported_context = None
            seen[class_] = res
            return res
        return [altered_clone(p) for p in self._parents]

    def __eq__(self, other):
        if not isinstance(other, MuranoType):
            return False
        return self.name == other.name and self.version == other.version

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash((self.name, self.version))

    @property
    def usage(self):
        return dsl_types.ClassUsages.Class

    @property
    def parents(self):
        return self._parents

    @property
    def methods(self):
        return self._methods

    @property
    def all_method_names(self):
        names = set(self.methods.keys())
        for c in self.ancestors():
            names.update(c.methods.keys())
        return tuple(names)

    @property
    def extension_class(self):
        return self._extension_class

    @extension_class.setter
    def extension_class(self, cls):
        self._extension_class = cls
        ctor = yaql_integration.get_class_factory_definition(cls, self)
        self.add_method('__init__', ctor)

    def add_method(self, name, payload, original_name=None):
        method = murano_method.MuranoMethod(self, name, payload, original_name)
        self._methods[name] = method
        self._context = None
        self._exported_context = None
        return method

    @property
    def properties(self):
        return self._properties

    @property
    def all_property_names(self):
        names = set(self.properties.keys())
        for c in self.ancestors():
            names.update(c.properties.keys())
        return tuple(names)

    def add_property(self, property_typespec):
        if not isinstance(property_typespec, murano_property.MuranoProperty):
            raise TypeError('property_typespec')
        self._properties[property_typespec.name] = property_typespec

    def _find_symbol_chains(self, func):
        queue = collections.deque([(self, ())])
        while queue:
            cls, path = queue.popleft()
            symbol = func(cls)
            segment = (symbol,) if symbol is not None else ()
            leaf = True
            for p in cls.parents:
                leaf = False
                queue.append((p, path + segment))
            if leaf:
                path += segment
                if path:
                    yield path

    def _resolve_imports(self, imports):
        seen = {self.name}
        for imp in helpers.list_value(imports):
            if imp in seen:
                continue
            type = helpers.resolve_type(imp, self)
            if type in seen:
                continue
            seen.add(imp)
            seen.add(type)
            yield type

    def _choose_symbol(self, func):
        chains = sorted(
            self._find_symbol_chains(func),
            key=lambda t: len(t))
        result = []
        for i in range(len(chains)):
            if chains[i][0] in result:
                continue
            add = True
            for j in range(i + 1, len(chains)):
                common = 0
                if not add:
                    break
                for p in range(len(chains[i])):
                    if chains[i][-p - 1] is chains[j][-p - 1]:
                        common += 1
                    else:
                        break
                if common == len(chains[i]):
                    add = False
                    break
            if add:
                result.append(chains[i][0])
        return result

    def find_method(self, name):
        return self._choose_symbol(lambda cls: cls.methods.get(name))

    def find_property(self, name):
        return self._choose_symbol(
            lambda cls: cls.properties.get(name))

    def find_static_property(self, name):
        def prop_func(cls):
            prop = cls.properties.get(name)
            if prop is not None and prop.usage == 'Static':
                return prop

        result = self._choose_symbol(prop_func)
        if len(result) < 1:
            raise exceptions.NoPropertyFound(name)
        elif len(result) > 1:
            raise exceptions.AmbiguousPropertyNameError(name)
        return result[0]

    def find_single_method(self, name):
        result = self.find_method(name)
        if len(result) < 1:
            raise exceptions.NoMethodFound(name)
        elif len(result) > 1:
            raise exceptions.AmbiguousMethodName(name)
        return result[0]

    def find_methods(self, predicate):
        result = list(filter(predicate, self.methods.values()))
        for c in self.ancestors():
            for method in c.methods.values():
                if predicate(method) and method not in result:
                    result.append(method)
        return result

    def find_properties(self, predicate):
        result = list(filter(predicate, self.properties.values()))
        for c in self.ancestors():
            for prop in c.properties.values():
                if predicate(prop) and prop not in result:
                    result.append(prop)
        return result

    def _iterate_unique_methods(self):
        for name in self.all_method_names:
            try:
                yield self.find_single_method(name)
            except exceptions.AmbiguousMethodName:
                def func(*args, **kwargs):
                    raise
                yield murano_method.MuranoMethod(
                    self, name, func, ephemeral=True)

    def find_single_property(self, name):
        result = self.find_property(name)
        if len(result) < 1:
            raise exceptions.NoPropertyFound(name)
        elif len(result) > 1:
            raise exceptions.AmbiguousPropertyNameError(name)
        return result[0]

    def invoke(self, name, this, args, kwargs, context=None):
        method = self.find_single_method(name)
        return method.invoke(this, args, kwargs, context)

    def is_compatible(self, obj):
        if isinstance(obj, (murano_object.MuranoObject,
                            dsl.MuranoObjectInterface,
                            dsl_types.MuranoTypeReference)):
            obj = obj.type
        if obj == self:
            return True
        return any(cls == self for cls in obj.ancestors())

    def __repr__(self):
        return 'MuranoClass({0}/{1})'.format(self.name, self.version)

    def _build_parent_remappings(self):
        """Remaps class parents.

        In case of multiple inheritance class may indirectly get several
        versions of the same class. It is reasonable to try to replace them
        with single version to avoid conflicts. We can do that when within
        versions that satisfy our class package requirements.
        But in order to merge several classes that are not our parents but
        grand parents we will need to modify classes that may be used
        somewhere else (with another set of requirements). We cannot do this.
        So instead we build translation table that will tell which ancestor
        class need to be replaced with which so that we minimize number of
        versions used for single class (or technically packages since version
        is a package attribute). For translation table to work there should
        be a method that returns all class virtual ancestors so that everybody
        will see them instead of accessing class parents directly and getting
        declared ancestors.
        """
        result = {}

        aggregation = {
            self.package.name: {(
                self.package,
                semantic_version.Spec('==' + str(self.package.version))
            )}
        }
        for cls, parent in helpers.traverse(
                ((self, parent) for parent in self._parents),
                lambda cp: ((cp[1], anc) for anc in cp[1].parents)):
            if cls.package != parent.package:
                requirement = cls.package.requirements[parent.package.name]
                aggregation.setdefault(parent.package.name, set()).add(
                    (parent.package, requirement))

        package_bindings = {}
        for versions in aggregation.values():
            mappings = self._remap_package(versions)
            package_bindings.update(mappings)

        for cls in helpers.traverse(self.parents, lambda c: c.parents):
            if cls.package in package_bindings:
                package2 = package_bindings[cls.package]
                cls2 = package2.classes[cls.name]
                result[cls] = cls2
        return result

    @staticmethod
    def _remap_package(versions):
        result = {}
        reverse_mappings = {}
        versions_list = sorted(versions, key=lambda x: x[0].version)
        i = 0
        while i < len(versions_list):
            package1, requirement1 = versions_list[i]
            dst_package = None
            for j, (package2, _) in enumerate(versions_list):
                if i == j:
                    continue
                if package2.version in requirement1 and (
                        dst_package is None or
                        dst_package.version < package2.version):
                    dst_package = package2
            if dst_package:
                result[package1] = dst_package
                reverse_mappings.setdefault(dst_package, []).append(package1)
                for package in reverse_mappings.get(package1, []):
                    result[package] = dst_package
                del versions_list[i]
            else:
                i += 1
        return result

    def ancestors(self):
        for c in helpers.traverse(self, lambda t: t.parents):
            if c is not self:
                yield c

    @property
    def context(self):
        if not self._context:
            ctx = None
            for imp in reversed(self._imports):
                if ctx is None:
                    ctx = imp.exported_context
                else:
                    ctx = helpers.link_contexts(ctx, imp.exported_context)

            if ctx is None:
                self._context = yaql_integration.create_empty_context()
            else:
                self._context = ctx.create_child_context()

            for m in self._iterate_unique_methods():
                if m.instance_stub:
                    self._context.register_function(
                        m.instance_stub, name=m.instance_stub.name)
                if m.static_stub:
                    self._context.register_function(
                        m.static_stub, name=m.static_stub.name)
        return self._context

    @property
    def exported_context(self):
        if not self._exported_context:
            self._exported_context = yaql_integration.create_empty_context()
            for m in self._iterate_unique_methods():
                if m.usage == dsl_types.MethodUsages.Extension:
                    if m.instance_stub:
                        self._exported_context.register_function(
                            m.instance_stub, name=m.instance_stub.name)
                    if m.static_stub:
                        self._exported_context.register_function(
                            m.static_stub, name=m.static_stub.name)
        return self._exported_context

    def get_meta(self, context):
        if self._meta_values is None:
            executor = helpers.get_executor()
            context = executor.create_type_context(
                self, caller_context=context)
            self._meta_values = dslmeta.merge_providers(
                self, lambda cls: cls._meta, context)
        return self._meta_values


class MuranoMetaClass(dsl_types.MuranoMetaClass, MuranoClass):
    _allowed_usages = {dsl_types.ClassUsages.Meta, dsl_types.ClassUsages.Class}

    def __init__(self, ns_resolver, name, package, parents, meta=None,
                 imports=None):
        super(MuranoMetaClass, self).__init__(
            ns_resolver, name, package, parents, meta, imports)
        self._cardinality = dsl_types.MetaCardinality.One
        self._targets = list(dsl_types.MetaCardinality.All)
        self._inherited = False

    @property
    def usage(self):
        return dsl_types.ClassUsages.Meta

    @property
    def cardinality(self):
        return self._cardinality

    @cardinality.setter
    def cardinality(self, value):
        self._cardinality = value

    @property
    def targets(self):
        return self._targets

    @targets.setter
    def targets(self, value):
        self._targets = value

    @property
    def inherited(self):
        return self._inherited

    @inherited.setter
    def inherited(self, value):
        self._inherited = value

    def __repr__(self):
        return 'MuranoMetaClass({0}/{1})'.format(self.name, self.version)


def create(data, package, name, ns_resolver):
    usage = data.get('Usage', dsl_types.ClassUsages.Class)
    if usage == dsl_types.ClassUsages.Class:
        return _create_class(MuranoClass, name, ns_resolver, data, package)
    elif usage == dsl_types.ClassUsages.Meta:
        return _create_meta_class(
            MuranoMetaClass, name, ns_resolver, data, package)
    else:
        raise ValueError(u'Invalid type Usage: "{}"'.format(usage))


def _create_class(cls, name, ns_resolver, data, package, *args, **kwargs):
    parent_class_names = data.get('Extends')
    parent_classes = []
    if parent_class_names:
        if not utils.is_sequence(parent_class_names):
            parent_class_names = [parent_class_names]
        for parent_name in parent_class_names:
            full_name = ns_resolver.resolve_name(str(parent_name))
            parent_classes.append(package.find_class(full_name))

    type_obj = cls(
        ns_resolver, name, package, parent_classes, data.get('Meta'),
        data.get('Import'), *args, **kwargs)

    properties = data.get('Properties') or {}
    for property_name, property_spec in properties.items():
        spec = murano_property.MuranoProperty(
            type_obj, property_name, property_spec)
        type_obj.add_property(spec)

    methods = data.get('Methods') or data.get('Workflow') or {}

    method_mappings = {
        'initialize': '.init',
        'destroy': '.destroy'
    }

    for method_name, payload in methods.items():
        type_obj.add_method(
            method_mappings.get(method_name, method_name), payload)

    return type_obj


def _create_meta_class(cls, name, ns_resolver, data, package, *args, **kwargs):
    cardinality = data.get('Cardinality', dsl_types.MetaCardinality.One)
    if cardinality not in dsl_types.MetaCardinality.All:
        raise ValueError(u'Invalid MetaClass Cardinality "{}"'.format(
            cardinality))
    applies_to = data.get('Applies', dsl_types.MetaTargets.All)
    if isinstance(applies_to, six.string_types):
        applies_to = [applies_to]
    if isinstance(applies_to, list):
        applies_to = set(applies_to)
    delta = applies_to - dsl_types.MetaTargets.All - {'All'}
    if delta:
        raise ValueError(u'Invalid MetaClass target(s) {}:'.format(
            ', '.join(map(u'"{}"'.format, delta)))
        )
    if 'All' in applies_to:
        applies_to = dsl_types.MetaTargets.All
    inherited = data.get('Inherited', False)
    if not isinstance(inherited, bool):
        raise ValueError('Invalid Inherited value. Must be true or false')

    meta_cls = _create_class(
        cls, name, ns_resolver, data, package, *args, **kwargs)
    meta_cls.targets = list(applies_to)
    meta_cls.cardinality = cardinality
    meta_cls.inherited = inherited
    return meta_cls


def weigh_type_hierarchy(cls):
    """Weighs classes in type hierarchy by their distance from the root

    :param cls: root of hierarchy
    :return: dictionary that has class name as keys and distance from the root
             a values. Root class has always a distance of 0. If the class
             (or different versions of that class) is achievable through
             several paths the shortest distance is used.
    """

    result = {}
    for c, w in helpers.traverse(
            [(cls, 0)], lambda t: six.moves.map(
                lambda p: (p, t[1] + 1), t[0].parents)):
        result.setdefault(c.name, w)
    return result
