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

import contextlib
import itertools
import traceback

import eventlet
import eventlet.event
from oslo_log import log as logging
import six
from yaql.language import exceptions as yaql_exceptions
from yaql.language import specs
from yaql.language import utils

from murano.dsl import attribute_store
from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_exception
from murano.dsl import dsl_types
from murano.dsl import exceptions as dsl_exceptions
from murano.dsl import helpers
from murano.dsl import object_store
from murano.dsl.principal_objects import stack_trace
from murano.dsl import serializer
from murano.dsl import yaql_integration

LOG = logging.getLogger(__name__)


class MuranoDslExecutor(object):
    def __init__(self, package_loader, context_manager, session=None):
        self._package_loader = package_loader
        self._context_manager = context_manager
        self._session = session
        self._attribute_store = attribute_store.AttributeStore()
        self._object_store = object_store.ObjectStore(self)
        self._locks = {}
        self._root_context_cache = {}
        self._static_properties = {}

    @property
    def object_store(self):
        return self._object_store

    @property
    def execution_session(self):
        return self._session

    @property
    def attribute_store(self):
        return self._attribute_store

    @property
    def package_loader(self):
        return self._package_loader

    @property
    def context_manager(self):
        return self._context_manager

    def invoke_method(self, method, this, context, args, kwargs,
                      skip_stub=False, invoke_action=True):
        if isinstance(this, dsl.MuranoObjectInterface):
            this = this.object
        kwargs = utils.filter_parameters_dict(kwargs)
        runtime_version = method.declaring_type.package.runtime_version
        yaql_engine = yaql_integration.choose_yaql_engine(runtime_version)
        if context is None or not skip_stub:
            actions_only = (context is None and not method.name.startswith('.')
                            and invoke_action)
            method_context = self.create_method_context(
                self.create_object_context(this, context), method)
            method_context[constants.CTX_SKIP_FRAME] = True
            method_context[constants.CTX_ACTIONS_ONLY] = actions_only

            stub = method.static_stub if isinstance(
                this, dsl_types.MuranoType) else method.instance_stub
            if stub is None:
                raise ValueError(
                    'Method {0} cannot be called on receiver {1}'.format(
                        method, this))

            real_this = this.real_this if isinstance(
                this, dsl_types.MuranoObject) else this.get_reference()
            return stub(yaql_engine, method_context, real_this)(
                *args, **kwargs)

        if context[constants.CTX_ACTIONS_ONLY] and not method.is_action:
            raise dsl_exceptions.MethodNotExposed(
                '{0} is not an action'.format(method.name))

        if method.is_static:
            obj_context = self.create_object_context(
                method.declaring_type, context)
        else:
            obj_context = self.create_object_context(this, context)
        context = self.create_method_context(obj_context, method)

        if isinstance(this, dsl_types.MuranoObject):
            if this.destroyed:
                raise dsl_exceptions.ObjectDestroyedError(this)
            this = this.real_this

        if method.arguments_scheme is not None:
            args, kwargs = self._canonize_parameters(
                method.arguments_scheme, args, kwargs, method.name, this)

        this_lock = this
        arg_values_for_lock = {}
        method_meta = [m for m in method.get_meta(context)
                       if m.type.name == ('io.murano.metadata.'
                                          'engine.Synchronize')]
        if method_meta:
            method_meta = method_meta[0]

        if method_meta:
            if not method_meta.get_property('onThis', context):
                this_lock = None
            for arg_name in method_meta.get_property('onArgs', context):
                arg_val = kwargs.get(arg_name)
                if arg_val is not None:
                    arg_values_for_lock[arg_name] = arg_val

        arg_values_for_lock = utils.filter_parameters_dict(arg_values_for_lock)

        with self._acquire_method_lock(method, this_lock, arg_values_for_lock):
            for i, arg in enumerate(args, 2):
                context[str(i)] = arg
            for key, value in kwargs.items():
                context[key] = value

            def call():
                if isinstance(method.body, specs.FunctionDefinition):
                    if isinstance(this, dsl_types.MuranoType):
                        native_this = this.get_reference()
                    else:
                        native_this = dsl.MuranoObjectInterface(this.cast(
                            method.declaring_type))
                    return method.body(
                        yaql_engine, context, native_this)(*args, **kwargs)
                else:
                    context[constants.CTX_NAMES_SCOPE] = \
                        method.declaring_type
                    return (None if method.body is None
                            else method.body.execute(context))

            if (not isinstance(method.body, specs.FunctionDefinition) or
                    not method.body.meta.get(constants.META_NO_TRACE)):
                with self._log_method(context, args, kwargs) as log:
                    result = call()
                    log(result)
                    return result
            else:
                return call()

    @contextlib.contextmanager
    def _acquire_method_lock(self, method, this, arg_val_dict):
        if this is None:
            if not arg_val_dict:
                # if neither "this" nor argument values are set then no
                # locking is needed
                key = None
            else:
                # if only the argument values are passed then find the lock
                # list only by the method
                key = (None, id(method))
        else:
            if method.is_static:
                # find the lock list by the type and method
                key = (id(method.declaring_type), id(method))
            else:
                # find the lock list by the object and method
                key = (this.object_id, id(method))
        thread_id = helpers.get_current_thread_id()
        while True:
            event, event_owner = None, None
            if key is None:  # no locking needed
                break

            lock_list = self._locks.setdefault(key, [])
            # lock list contains a list of tuples:
            # first item of each tuple is a dict with the values of locking
            # arguments (it is used for argument values comparison),
            # second item is an event to wait on,
            # third one is the owner thread id

            # If this lock list is empty it means no locks on this object and
            # method at all.
            for arg_vals, l_event, l_event_owner in lock_list:
                if arg_vals == arg_val_dict:
                    event = l_event
                    event_owner = l_event_owner
                    break

            if event:
                if event_owner == thread_id:
                    # this means a re-entrant lock: the tuple with the same
                    # value of the first element exists in the list, but it was
                    # acquired by the same green thread. We may proceed with
                    # the call in this case
                    event = None
                    break
                else:
                    event.wait()
            else:
                # this means either the lock list was empty or didn't contain a
                # tuple with the first element equal to arg_val_dict.
                # Then let's acquire a lock, i.e. create a new tuple and place
                # it into the list
                event = eventlet.event.Event()
                event_owner = thread_id
                lock_list.append((arg_val_dict, event, event_owner))
                break
        try:
            yield
        finally:
            if event is not None:
                lock_list.remove((arg_val_dict, event, event_owner))
                if len(lock_list) == 0:
                    del self._locks[key]
                event.send()

    @contextlib.contextmanager
    def _log_method(self, context, args, kwargs):
        method = helpers.get_current_method(context)
        param_gen = itertools.chain(
            (six.text_type(arg) for arg in args),
            (u'{0} => {1}'.format(name, value)
             for name, value in kwargs.items()))
        params_str = u', '.join(param_gen)
        method_name = '::'.join((method.declaring_type.name, method.name))
        thread_id = helpers.get_current_thread_id()
        caller_str = ''
        caller_ctx = helpers.get_caller_context(context)
        if caller_ctx is not None:
            frame = stack_trace.compose_stack_frame(caller_ctx)
            if frame['location']:
                caller_str = ' called from ' + stack_trace.format_frame(frame)

        LOG.trace(u'{thread}: Begin execution {method}({params}){caller}'
                  .format(thread=thread_id, method=method_name,
                          params=params_str, caller=caller_str))
        try:
            def log_result(result):
                LOG.trace(
                    u'{thread}: End execution {method} with result '
                    u'{result}'.format(
                        thread=thread_id, method=method_name, result=result))
            yield log_result
        except Exception as e:
            LOG.trace(
                u'{thread}: End execution {method} with exception '
                u'{exc}'.format(thread=thread_id, method=method_name, exc=e))
            raise

    @staticmethod
    def _canonize_parameters(arguments_scheme, args, kwargs,
                             method_name, receiver):
        arg_names = list(arguments_scheme.keys())
        parameter_values = {}
        varargs_arg = None
        vararg_values = []
        kwargs_arg = None
        kwarg_values = {}
        for name, definition in arguments_scheme.items():
            if definition.usage == dsl_types.MethodArgumentUsages.VarArgs:
                varargs_arg = name
                parameter_values[name] = vararg_values
            elif definition.usage == dsl_types.MethodArgumentUsages.KwArgs:
                kwargs_arg = name
                parameter_values[name] = kwarg_values

        for i, arg in enumerate(args):
            name = None if i >= len(arg_names) else arg_names[i]
            if name is None or name in (varargs_arg, kwargs_arg):
                if varargs_arg:
                    vararg_values.append(arg)
                else:
                    raise yaql_exceptions.NoMatchingMethodException(
                        method_name, receiver)
            else:
                parameter_values[name] = arg

        for name, value in utils.filter_parameters_dict(kwargs).items():
            if name in arguments_scheme and name not in (
                    varargs_arg, kwargs_arg):
                parameter_values[name] = value
            elif kwargs_arg:
                kwarg_values[name] = value
            else:
                raise yaql_exceptions.NoMatchingMethodException(
                    method_name, receiver)
        return tuple(), parameter_values

    def load(self, data):
        with helpers.with_object_store(self.object_store):
            return self._load(data)

    def _load(self, data):
        if not isinstance(data, dict):
            raise TypeError()
        self._attribute_store.load(data.get(constants.DM_ATTRIBUTES) or [])
        model = data.get(constants.DM_OBJECTS)
        if model is None:
            result = None
        else:
            result = self._object_store.load(model, None, keep_ids=True)
        model_copy = data.get(constants.DM_OBJECTS_COPY)
        if model_copy:
            self._object_store.load(model_copy, None, keep_ids=True)
        return dsl.MuranoObjectInterface.create(result)

    def signal_destruction_dependencies(self, *objects):
        if not objects:
            return
        elif len(objects) > 1:
            return helpers.parallel_select(
                objects, self.signal_destruction_dependencies)

        obj = objects[0]
        if obj.destroyed:
            return
        for dependency in obj.destruction_dependencies:
            try:
                handler = dependency['handler']
                if handler:
                    subscriber = dependency['subscriber']
                    if subscriber:
                        subscriber = subscriber()
                    if (subscriber and
                            subscriber.initialized and
                            not subscriber.destroyed):
                        method = subscriber.type.find_single_method(handler)
                        self.invoke_method(
                            method, subscriber, None, [obj], {},
                            invoke_action=False)
            except Exception as e:
                LOG.warning('Muted exception during destruction dependency '
                            'execution in {0}: {1}'.format(obj, e),
                            exc_info=True)
        obj.load_dependencies(None)

    def destroy_objects(self, *objects):
        if not objects:
            return
        elif len(objects) > 1:
            return helpers.parallel_select(
                objects, self.destroy_objects)

        obj = objects[0]
        if obj.destroyed:
            return
        methods = obj.type.find_methods(lambda m: m.name == '.destroy')
        for method in methods:
            try:
                method.invoke(obj, (), {}, None)
            except Exception as e:
                if isinstance(e, dsl_exception.MuranoPlException):
                    tb = e.format(prefix='  ')
                else:
                    tb = traceback.format_exc()
                LOG.warning(
                    'Muted exception during execution of .destroy '
                    'on {0}: {1}'.format(obj, tb), exc_info=True)

    def create_root_context(self, runtime_version):
        context = self._root_context_cache.get(runtime_version)
        if not context:
            context = self.context_manager.create_root_context(runtime_version)
            self._root_context_cache[runtime_version] = context
        return context

    def create_package_context(self, package):
        root_context = self.create_root_context(package.runtime_version)
        context = helpers.link_contexts(
            root_context,
            self.context_manager.create_package_context(package))
        return context

    def create_type_context(self, murano_type, caller_context=None):
        package_context = self.create_package_context(
            murano_type.package)
        context = helpers.link_contexts(
            package_context,
            self.context_manager.create_type_context(
                murano_type)).create_child_context()
        context[constants.CTX_TYPE] = murano_type
        if caller_context:
            context[constants.CTX_NAMES_SCOPE] = caller_context[
                constants.CTX_NAMES_SCOPE]
        return context

    def create_object_context(self, obj, caller_context=None):
        if isinstance(obj, dsl_types.MuranoClass):
            obj_type = obj
            obj = None
        else:
            obj_type = obj.type
        class_context = self.create_type_context(obj_type)
        if obj is not None:
            context = helpers.link_contexts(
                class_context, self.context_manager.create_object_context(
                    obj)).create_child_context()
            context[constants.CTX_THIS] = obj.real_this
            context['this'] = obj.real_this
            context[''] = obj.real_this
        else:
            context = class_context.create_child_context()
            type_ref = obj_type.get_reference()
            context[constants.CTX_THIS] = type_ref
            context['this'] = type_ref
            context[''] = type_ref

        if caller_context is not None:
            caller = caller_context
            while caller is not None and caller[constants.CTX_SKIP_FRAME]:
                caller = caller[constants.CTX_CALLER_CONTEXT]
            context[constants.CTX_NAMES_SCOPE] = caller_context[
                constants.CTX_NAMES_SCOPE]
            context[constants.CTX_CALLER_CONTEXT] = caller
            context[constants.CTX_ALLOW_PROPERTY_WRITES] = caller_context[
                constants.CTX_ALLOW_PROPERTY_WRITES]
        else:
            context[constants.CTX_NAMES_SCOPE] = obj_type
        return context

    @staticmethod
    def create_method_context(object_context, method):
        context = object_context.create_child_context()
        context[constants.CTX_CURRENT_METHOD] = method
        return context

    def run(self, cls, method_name, this, args, kwargs):
        with helpers.with_object_store(self.object_store):
            return cls.invoke(method_name, this, args, kwargs)

    def get_static_property(self, murano_type, name, context):
        prop = murano_type.find_static_property(name)
        cls = prop.declaring_type
        value = self._static_properties.get(prop, prop.default)
        return prop.transform(value, cls, None, context)

    def set_static_property(self, murano_type, name, value,
                            context, dry_run=False):
        prop = murano_type.find_static_property(name)
        cls = prop.declaring_type
        value = prop.transform(value, cls, None, context)
        if not dry_run:
            self._static_properties[prop] = prop.finalize(
                value, cls, context)

    def finalize(self, model_root=None):
        # NOTE(ksnihyr): should be no-except
        try:
            if model_root:
                used_objects = serializer.collect_objects(model_root)
                self.object_store.prepare_finalize(used_objects)
                model = serializer.serialize_model(model_root, self)
                self.object_store.finalize()
            else:
                model = None
                self.object_store.prepare_finalize(None)
                self.object_store.finalize()
            self._static_properties.clear()
            return model
        except Exception as e:
            LOG.exception(
                "Exception %s occurred"
                " during MuranoDslExecutor finalization", e)
            return None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finalize()
