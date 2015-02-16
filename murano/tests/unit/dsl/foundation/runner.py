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
import types

from murano.dsl import dsl_exception
from murano.dsl import executor
from murano.dsl import murano_object
from murano.dsl import serializer
from murano.engine import environment
from murano.tests.unit.dsl.foundation import object_model


class Runner(object):
    class DslObjectWrapper(object):
        def __init__(self, obj, runner):
            self._runner = runner
            if isinstance(obj, types.StringTypes):
                self._object_id = obj
            elif isinstance(obj, (object_model.Object, object_model.Ref)):
                self._object_id = obj.id
            elif isinstance(obj, murano_object.MuranoObject):
                self._object_id = obj.object_id
            else:
                raise ValueError(
                    'obj must be object ID string, MuranoObject or one of '
                    'object_model helper classes (Object, Ref)')
            self._preserve_exception = False

        def __getattr__(self, item):
            def call(*args, **kwargs):
                return self._runner._execute(
                    item, self._object_id, *args, **kwargs)
            if item.startswith('test'):
                return call

    def __init__(self, model, class_loader):
        if isinstance(model, types.StringTypes):
            model = object_model.Object(model)
        model = object_model.build_model(model)
        if 'Objects' not in model:
            model = {'Objects': model}

        self.executor = executor.MuranoDslExecutor(
            class_loader, environment.Environment())
        self._root = self.executor.load(model)

    def _execute(self, name, object_id, *args, **kwargs):
        obj = self.executor.object_store.get(object_id)
        try:
            final_args = []
            for arg in args:
                if isinstance(arg, object_model.Object):
                    arg = object_model.build_model(arg)
                final_args.append(arg)
            for name, arg in kwargs.iteritems():
                if isinstance(arg, object_model.Object):
                    arg = object_model.build_model(arg)
                final_args.append({name: arg})
            return obj.type.invoke(name, self.executor, obj, tuple(final_args))
        except dsl_exception.MuranoPlException as e:
            if not self.preserve_exception:
                original_exception = getattr(e, 'original_exception', None)
                if original_exception and not isinstance(
                        original_exception, dsl_exception.MuranoPlException):
                    exc_traceback = getattr(
                        e, 'original_traceback', None) or sys.exc_info()[2]
                    raise type(original_exception), original_exception, \
                        exc_traceback
            raise

    def __getattr__(self, item):
        if item.startswith('test'):
            return getattr(Runner.DslObjectWrapper(self._root, self), item)

    def on(self, obj):
        return Runner.DslObjectWrapper(obj, self)

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
