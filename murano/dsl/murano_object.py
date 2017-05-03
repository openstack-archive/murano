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


from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl.principal_objects import garbage_collector
from murano.dsl import yaql_integration


class MuranoObject(dsl_types.MuranoObject):
    def __init__(self, murano_class, owner, object_id=None, name=None,
                 known_classes=None, this=None, metadata=None):
        self._initialized = False
        self._destroyed = False
        if known_classes is None:
            known_classes = {}
        if this is None:
            self._owner = owner
        self._object_id = object_id or helpers.generate_id()
        self._type = murano_class
        self._properties = {}
        self._parents = {}
        self._this = this
        self._name = name
        self._extension = None
        self._executor = helpers.weak_ref(helpers.get_executor())
        self._config = murano_class.package.get_class_config(
            murano_class.name)
        self._metadata = metadata
        if not isinstance(self._config, dict):
            self._config = {}
        known_classes[murano_class.name] = self
        for parent_class in murano_class.parents:
            name = parent_class.name
            if name not in known_classes:
                obj = MuranoObject(
                    parent_class, owner,
                    object_id=self._object_id,
                    known_classes=known_classes, this=self.real_this)

                self._parents[name] = known_classes[name] = obj
            else:
                self._parents[name] = known_classes[name]
        self._destruction_dependencies = []

    @property
    def extension(self):
        return self._extension

    @property
    def name(self):
        return self.real_this._name

    @property
    def metadata(self):
        return self.real_this._metadata

    @extension.setter
    def extension(self, value):
        self._extension = value

    def initialize(self, context, params, used_names=None):
        context = context.create_child_context()
        context[constants.CTX_ALLOW_PROPERTY_WRITES] = True
        object_store = helpers.get_object_store()
        for property_name in self.type.properties:
            spec = self.type.properties[property_name]
            if spec.usage == dsl_types.PropertyUsages.Config:
                if property_name in self._config:
                    property_value = self._config[property_name]
                else:
                    property_value = dsl.NO_VALUE
                self.set_property(property_name, property_value,
                                  dry_run=self._initialized)

        init = self.type.methods.get('.init')
        used_names = used_names or set()
        names = set(self.type.properties)
        if init:
            names.update(init.arguments_scheme.keys())
        last_errors = len(names)
        init_args = {}
        while True:
            errors = 0
            for property_name in names:
                if init and property_name in init.arguments_scheme:
                    spec = init.arguments_scheme[property_name]
                    is_init_arg = True
                else:
                    spec = self.type.properties[property_name]
                    is_init_arg = False

                if property_name in used_names:
                    continue
                if spec.usage in (dsl_types.PropertyUsages.Config,
                                  dsl_types.PropertyUsages.Static):
                    used_names.add(property_name)
                    continue
                if spec.usage == dsl_types.PropertyUsages.Runtime:
                    if not spec.has_default:
                        used_names.add(property_name)
                        continue
                    property_value = dsl.NO_VALUE
                else:
                    property_value = params.get(property_name, dsl.NO_VALUE)
                try:
                    if is_init_arg:
                        init_args[property_name] = property_value
                    else:
                        self.set_property(
                            property_name, property_value, context,
                            dry_run=self._initialized)
                    used_names.add(property_name)
                except exceptions.UninitializedPropertyAccessError:
                    errors += 1
                except exceptions.ContractViolationException:
                    if spec.usage != dsl_types.PropertyUsages.Runtime:
                        raise
            if not errors:
                break
            if errors >= last_errors:
                raise exceptions.CircularExpressionDependenciesError()
            last_errors = errors

        if (not object_store.initializing and
                self._extension is None and
                not self._initialized and
                not self._destroyed and
                not helpers.is_objects_dry_run_mode()):
            method = self.type.methods.get('__init__')
            if method:
                filtered_params = yaql_integration.filter_parameters(
                    method.body, **params)
                yield lambda: method.invoke(
                    self, filtered_params[0], filtered_params[1], context)

        for parent in self._parents.values():
            for t in parent.initialize(context, params, used_names):
                yield t

        def run_init():
            if init:
                context[constants.CTX_ARGUMENT_OWNER] = self.real_this
                init.invoke(self.real_this, (), init_args,
                            context.create_child_context())
            self._initialized = True

        if (not object_store.initializing and
                not helpers.is_objects_dry_run_mode() and
                not self._initialized and
                not self._destroyed):
            yield run_init

    @property
    def object_id(self):
        return self._object_id

    @property
    def type(self):
        return self._type

    @property
    def owner(self):
        if self._this is None:
            return self._owner
        else:
            return self.real_this.owner

    @property
    def real_this(self):
        return self._this or self

    @property
    def executor(self):
        return self._executor()

    @property
    def initialized(self):
        return self._initialized

    @property
    def destruction_dependencies(self):
        return self._destruction_dependencies

    def load_dependencies(self, dependencies):
        self._destruction_dependencies = []
        if not dependencies:
            return
        destruction_dependencies = dependencies.get('onDestruction', [])
        object_store = helpers.get_object_store()
        for record in destruction_dependencies:
            subscriber_id = record['subscriber']
            subscriber = object_store.get(subscriber_id)
            if not subscriber:
                continue
            garbage_collector.GarbageCollector.subscribe_destruction(
                self, subscriber, record.get('handler'))

    def get_property(self, name, context=None):
        start_type, derived = self.type, False
        caller_class = None if not context else helpers.get_type(context)
        if caller_class is not None and caller_class.is_compatible(self):
            start_type, derived = caller_class, True

        declared_properties = start_type.find_properties(
            lambda p: p.name == name)
        if len(declared_properties) > 0:
            spec = self.real_this.type.find_single_property(name)
            if spec.usage == dsl_types.PropertyUsages.Static:
                return self.executor.get_static_property(
                    spec.declaring_type, name, context)
            else:
                return self.real_this._get_property_value(name)
        elif derived:
            return self.cast(caller_class)._get_property_value(name)
        else:
            raise exceptions.PropertyReadError(name, start_type)

    def _get_property_value(self, name):
        try:
            return self._properties[name]
        except KeyError:
            raise exceptions.UninitializedPropertyAccessError(
                name, self.type)

    def set_property(self, name, value, context=None, dry_run=False):
        start_type, derived = self.real_this.type, False
        caller_class = None if not context else helpers.get_type(context)
        if caller_class is not None and caller_class.is_compatible(self):
            start_type, derived = caller_class, True
        if context is None:
            context = self.executor.create_object_context(self)
        declared_properties = start_type.find_properties(
            lambda p: p.name == name)
        if len(declared_properties) > 0:
            ultimate_spec = self.real_this.type.find_single_property(name)
            property_list = list(self._list_properties(name))
            for spec in property_list:
                if (caller_class is not None and not
                        helpers.are_property_modifications_allowed(context) and
                        (spec.usage not in dsl_types.PropertyUsages.Writable or
                            not derived)):
                    raise exceptions.NoWriteAccessError(name)

                if spec.usage == dsl_types.PropertyUsages.Static:
                    default = None
                else:
                    default = self._config.get(name, spec.default)

                if spec is ultimate_spec:
                    value = spec.transform(
                        value, self.real_this,
                        self.real_this, context, default=default,
                        finalize=len(property_list) == 1)
                else:
                    spec.validate(value, self.real_this, context, default)
            if len(property_list) > 1:
                value = ultimate_spec.finalize(value, self.real_this, context)
            if ultimate_spec.usage == dsl_types.PropertyUsages.Static:
                self.executor.set_static_property(
                    ultimate_spec.declaring_type, name, value, context,
                    dry_run=dry_run)
            elif not dry_run:
                self.real_this._properties[name] = value
        elif derived:
            if not dry_run:
                obj = self.cast(caller_class)
                obj._properties[name] = value
        else:
            raise exceptions.PropertyWriteError(name, start_type)

    def cast(self, cls):
        for p in helpers.traverse(self, lambda t: t._parents.values()):
            if p.type == cls:
                return p
        raise TypeError('Cannot cast {0} to {1}'.format(self.type, cls))

    def _list_properties(self, name):
        for p in helpers.traverse(
                self.real_this, lambda t: t._parents.values()):
            if name in p.type.properties:
                yield p.type.properties[name]

    def __repr__(self):
        return '<{0}/{1} {2} ({3})>'.format(
            self.type.name, self.type.version, self.object_id, id(self))

    def to_dictionary(self, include_hidden=False,
                      serialization_type=dsl_types.DumpTypes.Serializable,
                      allow_refs=False, with_destruction_dependencies=False):
        context = helpers.get_context()
        result = {}
        for parent in self._parents.values():
            result.update(parent.to_dictionary(
                include_hidden, dsl_types.DumpTypes.Serializable,
                allow_refs))
        skip_usages = (dsl_types.PropertyUsages.Runtime,
                       dsl_types.PropertyUsages.Config)
        for property_name in self.type.properties:
            if property_name in self.real_this._properties:
                spec = self.type.properties[property_name]
                if spec.usage not in skip_usages or include_hidden:
                    prop_value = self.real_this._properties[property_name]
                    if isinstance(prop_value, MuranoObject) and allow_refs:
                        meta = [m for m in spec.get_meta(context)
                                if m.type.name == ('io.murano.metadata.'
                                                   'engine.Serialize')]
                        if meta and meta[0].get_property(
                                'as', context) == 'reference':
                            prop_value = prop_value.object_id
                    result[property_name] = prop_value
        if serialization_type == dsl_types.DumpTypes.Inline:
            result.pop('?')
            result = {
                self.type: result,
                'id': self.object_id,
                'name': self.name,
                'metadata': self.metadata
            }
            header = result
        else:
            if serialization_type == dsl_types.DumpTypes.Mixed:
                result.update({'?': {
                    'type': self.type,
                    'id': self.object_id,
                    'name': self.name,
                    'metadata': self.metadata
                }})
            else:
                result.update({'?': {
                    'type': helpers.format_type_string(self.type),
                    'id': self.object_id,
                    'name': self.name,
                    'metadata': self.metadata
                }})
            header = result['?']
        if self.destroyed:
            header['destroyed'] = True
        if with_destruction_dependencies:
            dds = []
            for record in self.destruction_dependencies:
                subscriber = record['subscriber']()
                if not subscriber or self.executor.object_store.is_doomed(
                        subscriber):
                    continue
                dds.append({
                    'subscriber': subscriber.object_id,
                    'handler': record['handler']
                })
            if dds:
                header.setdefault('dependencies', {})['onDestruction'] = dds
        return result

    def mark_destroyed(self, clear_data=False):
        self._destroyed = True
        self._suppress__del__ = None
        if clear_data or not self.initialized:
            self._extension = None
            self._properties = None
            self._owner = None
            self._destruction_dependencies = None
            self._this = None
        for p in self._parents.values():
            p.mark_destroyed(clear_data)

    @property
    def destroyed(self):
        return self._destroyed


class RecyclableMuranoObject(MuranoObject):
    def __init__(self, *args, **kwargs):
        # Create self-reference to prevent __del__ from being called
        # automatically when there are no other objects referring to this one.
        # Without this reference __del__ will get called immediately after
        # reference counter will go to 0 and the object will put itself into
        # pending list creating another reference to itself and thus preventing
        # its child objects from being deleted. After the .destroy method
        # child objects will become eligible for destruction but will be
        # unable to use find() method since their owner will be destroyed
        # and collected at that point. With this reference gc.collect()
        # will collect the whole object graph at once and then we could
        # sort it and destroy in the correct order so that child objects
        # will be destroyed first.

        self._suppress__del__ = self
        super(RecyclableMuranoObject, self).__init__(*args, **kwargs)

    def __del__(self):
        # For Py2 the purpose of __del__ (in combination with _suppress__del__)
        # method is just to prevent object from being released automatically.
        # In Py3 the gc.collect list will be empty and __del__ will be called
        # for objects that were not destroyed yet.
        if self._this is None and self._initialized and not self._destroyed:
            self.executor.object_store.schedule_object_destruction(self)

    def mark_destroyed(self, clear_data=False):
        self.executor.attribute_store.forget_object(self)
        super(RecyclableMuranoObject, self).mark_destroyed(clear_data)
