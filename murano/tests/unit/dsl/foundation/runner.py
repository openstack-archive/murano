# Copyright (c) 2014 Mirantis, Inc.
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

import sys

import six

from murano.dsl import context_manager
from murano.dsl import dsl
from murano.dsl import dsl_exception
from murano.dsl import dsl_types
from murano.dsl import executor
from murano.dsl import helpers
from murano.dsl import murano_object
from murano.dsl import serializer
from murano.dsl import yaql_integration
from murano.engine import execution_session
from murano.engine.system import yaql_functions
from murano.tests.unit.dsl.foundation import object_model


class TestContextManager(context_manager.ContextManager):
    def __init__(self, functions):
        self.__functions = functions

    def create_root_context(self, runtime_version):
        root_context = super(TestContextManager, self).create_root_context(
            runtime_version)
        context = helpers.link_contexts(
            root_context, yaql_functions.get_context(runtime_version))
        context = context.create_child_context()
        for name, func in self.__functions.items():
            context.register_function(func, name)
        return context


class Runner(object):
    class DslObjectWrapper(object):
        def __init__(self, obj, runner):
            self._runner = runner
            if isinstance(obj, six.string_types + (dsl_types.MuranoType,)):
                pass
            elif isinstance(obj, (object_model.Object, object_model.Ref)):
                obj = obj.id
            elif isinstance(obj, murano_object.MuranoObject):
                obj = obj.object_id
            else:
                raise ValueError(
                    'obj must be object ID string, MuranoObject, MuranoType '
                    'or one of object_model helper classes (Object, Ref)')
            if isinstance(obj, six.string_types):
                self._receiver = runner.executor.object_store.get(obj)
            else:
                self._receiver = obj

            self._preserve_exception = False

        def __getattr__(self, item):
            def call(*args, **kwargs):
                return self._runner._execute(
                    item, self._receiver, *args, **kwargs)
            if item.startswith('test'):
                return call

    def __init__(self, model, package_loader, functions):
        if isinstance(model, six.string_types):
            model = object_model.Object(model)
        model = object_model.build_model(model)
        if 'Objects' not in model:
            model = {'Objects': model}

        self.executor = executor.MuranoDslExecutor(
            package_loader, TestContextManager(functions),
            execution_session.ExecutionSession())
        self._root = self.executor.load(model)
        if self._root:
            self._root = self._root.object
        if 'ObjectsCopy' in model:
            self.executor.object_store.cleanup()

    def _execute(self, name, obj, *args, **kwargs):
        try:
            final_args = []
            final_kwargs = {}
            for arg in args:
                if isinstance(arg, object_model.Object):
                    arg = object_model.build_model(arg)
                final_args.append(arg)
            for name, arg in kwargs.items():
                if isinstance(arg, object_model.Object):
                    arg = object_model.build_model(arg)
                final_kwargs[name] = arg
            cls = obj if isinstance(obj, dsl_types.MuranoType) else obj.type
            runtime_version = cls.package.runtime_version
            yaql_engine = yaql_integration.choose_yaql_engine(runtime_version)
            with helpers.with_object_store(self.executor.object_store):
                return dsl.to_mutable(cls.invoke(
                    name, obj, tuple(final_args), final_kwargs), yaql_engine)
        except dsl_exception.MuranoPlException as e:
            if not self.preserve_exception:
                original_exception = getattr(e, 'original_exception', None)
                if original_exception and not isinstance(
                        original_exception, dsl_exception.MuranoPlException):
                    exc_traceback = getattr(
                        e, 'original_traceback', None) or sys.exc_info()[2]
                    six.reraise(
                        type(original_exception),
                        original_exception,
                        exc_traceback)
            raise

    def __getattr__(self, item):
        if item.startswith('test'):
            return getattr(Runner.DslObjectWrapper(self._root, self), item)

    def on(self, obj):
        return Runner.DslObjectWrapper(obj, self)

    def on_class(self, class_name):
        cls = self.executor.package_loader.load_class_package(
            class_name, helpers.parse_version_spec(None)).find_class(
            class_name, False)
        return Runner.DslObjectWrapper(cls, self)

    @property
    def root(self):
        return self._root

    @property
    def serialized_model(self):
        return serializer.serialize_model(self._root, self.executor)

    @property
    def preserve_exception(self):
        return self._preserve_exception

    @preserve_exception.setter
    def preserve_exception(self, value):
        self._preserve_exception = value

    def session(self):
        return helpers.with_object_store(self.executor.object_store)
