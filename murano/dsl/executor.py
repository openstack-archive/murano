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

import collections
import contextlib
import itertools
import weakref

import eventlet
import eventlet.event
from oslo_log import log as logging
import six
from yaql.language import exceptions as yaql_exceptions
from yaql.language import specs
from yaql.language import utils

from murano.common.i18n import _LW
from murano.dsl import attribute_store
from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.dsl import object_store
from murano.dsl.principal_objects import stack_trace
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

    @property
    def object_store(self):
        return self._object_store

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
                      skip_stub=False):
        with helpers.execution_session(self._session):
            return self._invoke_method(
                method, this, context, args, kwargs, skip_stub=skip_stub)

    def _invoke_method(self, method, this, context, args, kwargs,
                       skip_stub=False):
        if isinstance(this, dsl.MuranoObjectInterface):
            this = this.object
        kwargs = utils.filter_parameters_dict(kwargs)
        runtime_version = method.declaring_type.package.runtime_version
        yaql_engine = yaql_integration.choose_yaql_engine(runtime_version)
        if context is None or not skip_stub:
            actions_only = context is None and not method.name.startswith('.')
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

            return stub(yaql_engine, method_context, this.real_this)(
                *args, **kwargs)

        if (context[constants.CTX_ACTIONS_ONLY] and method.usage !=
                dsl_types.MethodUsages.Action):
            raise Exception('{0} is not an action'.format(method.name))

        if method.is_static:
            obj_context = self.create_object_context(
                method.declaring_type, context)
        else:
            obj_context = self.create_object_context(this, context)
        context = self.create_method_context(obj_context, method)

        if isinstance(this, dsl_types.MuranoObject):
            this = this.real_this

        if method.arguments_scheme is not None:
            args, kwargs = self._canonize_parameters(
                method.arguments_scheme, args, kwargs, method.name, this)

        with self._acquire_method_lock(method, this):
            for i, arg in enumerate(args, 2):
                context[str(i)] = arg
            for key, value in six.iteritems(kwargs):
                context[key] = value

            def call():
                if isinstance(method.body, specs.FunctionDefinition):
                    if isinstance(this, dsl_types.MuranoType):
                        native_this = this.get_reference()
                    else:
                        native_this = dsl.MuranoObjectInterface(this.cast(
                            method.declaring_type), self)
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
    def _acquire_method_lock(self, method, this):
        method_id = id(method)
        if method.is_static:
            this_id = id(method.declaring_type)
        else:
            this_id = this.object_id
        thread_id = helpers.get_current_thread_id()
        while True:
            event, event_owner = self._locks.get(
                (method_id, this_id), (None, None))
            if event:
                if event_owner == thread_id:
                    event = None
                    break
                else:
                    event.wait()
            else:
                event = eventlet.event.Event()
                self._locks[(method_id, this_id)] = (event, thread_id)
                break
        try:
            yield
        finally:
            if event is not None:
                del self._locks[(method_id, this_id)]
                event.send()

    @contextlib.contextmanager
    def _log_method(self, context, args, kwargs):
        method = helpers.get_current_method(context)
        param_gen = itertools.chain(
            (six.text_type(arg) for arg in args),
            (u'{0} => {1}'.format(name, value)
             for name, value in six.iteritems(kwargs)))
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
        for name, definition in six.iteritems(arguments_scheme):
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

        for name, value in six.iteritems(utils.filter_parameters_dict(kwargs)):
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
        with helpers.execution_session(self._session):
            return self._load(data)

    def _load(self, data):
        if not isinstance(data, dict):
            raise TypeError()
        self._attribute_store.load(data.get(constants.DM_ATTRIBUTES) or [])
        result = self._object_store.load(data.get(constants.DM_OBJECTS), None)
        if result is None:
            return None
        return dsl.MuranoObjectInterface(result, executor=self)

    def cleanup(self, data):
        with helpers.execution_session(self._session):
            return self._cleanup(data)

    def _cleanup(self, data):
        objects_copy = data.get(constants.DM_OBJECTS_COPY)
        if not objects_copy:
            return
        gc_object_store = object_store.ObjectStore(self)
        gc_object_store.load(objects_copy, None)
        objects_to_clean = []
        for object_id in self._list_potential_object_ids(objects_copy):
            if (gc_object_store.has(object_id) and
                    not self._object_store.has(object_id)):
                obj = gc_object_store.get(object_id)
                objects_to_clean.append(obj)
        if objects_to_clean:
            for obj in objects_to_clean:
                self._destroy_object(obj)

    def cleanup_orphans(self, alive_object_ids):
        with helpers.execution_session(self._session):
            orphan_ids = self._collect_orphans(alive_object_ids)
            self._destroy_orphans(orphan_ids)
            return len(orphan_ids)

    def _collect_orphans(self, alive_object_ids):
        orphan_ids = []
        for obj_id in self._object_store.iterate():
            if obj_id not in alive_object_ids:
                orphan_ids.append(obj_id)
        return orphan_ids

    def _destroy_orphans(self, orphan_ids):
        for obj_id in orphan_ids:
            self._destroy_object(self._object_store.get(obj_id))
            self._object_store.remove(obj_id)

    def _destroy_object(self, obj):
        methods = obj.type.find_methods(lambda m: m.name == '.destroy')
        for method in methods:
            try:
                method.invoke(self, obj, (), {}, None)
            except Exception as e:
                LOG.warning(_LW(
                    'Muted exception during execution of .destroy '
                    'on {0}: {1}').format(obj, e), exc_info=True)

    def _list_potential_object_ids(self, data):
        if isinstance(data, dict):
            for val in six.itervalues(data):
                for res in self._list_potential_object_ids(val):
                    yield res
            sys_dict = data.get('?')
            if (isinstance(sys_dict, dict) and
                    sys_dict.get('id') and sys_dict.get('type')):
                yield sys_dict['id']
        elif isinstance(data, collections.Iterable) and not isinstance(
                data, six.string_types):
            for val in data:
                for res in self._list_potential_object_ids(val):
                    yield res

    def create_root_context(self, runtime_version):
        context = self._root_context_cache.get(runtime_version)
        if not context:
            context = self.context_manager.create_root_context(runtime_version)
            context = context.create_child_context()
            context[constants.CTX_EXECUTOR] = weakref.ref(self)
            context[constants.CTX_PACKAGE_LOADER] = weakref.ref(
                self._package_loader)
            context[constants.CTX_EXECUTION_SESSION] = self._session
            context[constants.CTX_ATTRIBUTE_STORE] = weakref.ref(
                self._attribute_store)
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
