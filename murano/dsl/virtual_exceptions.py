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

import six

from murano.dsl import constants
from murano.dsl import dsl_exception
from murano.dsl import expressions
from murano.dsl import helpers
from murano.dsl import macros
from murano.dsl.principal_objects import stack_trace
from murano.dsl import yaql_integration


class ThrowMacro(expressions.DslExpression):
    def __init__(self, Throw, Message=None, Extra=None, Cause=None):
        if not Throw:
            raise ValueError()
        if not isinstance(Throw, list):
            Throw = [Throw]

        self._names = Throw
        self._message = Message
        self._extra = Extra or {}
        self._cause = Cause

    def _resolve_names(self, names, context):
        murano_class = helpers.get_type(context)
        for name in names:
            yield murano_class.namespace_resolver.resolve_name(name)

    def execute(self, context):
        stacktrace = stack_trace.create_stack_trace(context, False)
        cause = None
        if self._cause:
            cause = helpers.evaluate(self._cause, context).get_property(
                'nativeException')
        raise dsl_exception.MuranoPlException(
            list(self._resolve_names(helpers.evaluate(self._names, context),
                                     context)),
            helpers.evaluate(self._message, context),
            stacktrace, self._extra, cause)

    def __unicode__(self):
        if self._message:
            return u'Throw {0}: {1}'.format(self._names, self._message)
        return u'Throw ' + six.text_type(self._names)


class CatchBlock(expressions.DslExpression):
    def __init__(self, With=None, As=None, Do=None):
        if With is not None and not isinstance(With, list):
            With = [With]
        self._with = With
        self._as = As
        self._code_block = None if Do is None else macros.CodeBlock(Do)

    def _resolve_names(self, names, context):
        murano_class = helpers.get_type(context)
        for name in names:
            yield murano_class.namespace_resolver.resolve_name(name)

    def execute(self, context):
        exception = helpers.get_current_exception(context)
        names = (
            None if self._with is None
            else list(self._resolve_names(self._with, context))
        )

        for name in exception.names:
            if self._with is None or name in names:
                if self._code_block:
                    if self._as:
                        wrapped = self._wrap_internal_exception(
                            exception, context, name)
                        context[self._as] = wrapped
                    self._code_block.execute(context)
                return True
        return False

    def _wrap_internal_exception(self, exception, context, name):
        obj = yaql_integration.call_func(context, 'new', 'io.murano.Exception')
        obj.set_property('name', name)
        obj.set_property('message', exception.message)
        obj.set_property('stackTrace', exception.stacktrace)
        obj.set_property('extra', exception.extra)
        obj.set_property('nativeException', exception)
        return obj


class TryBlockMacro(expressions.DslExpression):
    def __init__(self, Try, Catch=None, Finally=None, Else=None):
        self._try_block = macros.CodeBlock(Try)
        self._catch_block = None
        if Catch is not None:
            if not isinstance(Catch, list):
                Catch = [Catch]
            self._catch_block = [CatchBlock(**c) for c in Catch]
        self._finally_block = (
            None if Finally is None
            else macros.CodeBlock(Finally))
        self._else_block = (
            None if Else is None
            else macros.CodeBlock(Else))

    def execute(self, context):
        try:
            self._try_block.execute(context)
        except dsl_exception.MuranoPlException as e:
            caught = False
            if self._catch_block:
                try:
                    context[constants.CTX_CURRENT_EXCEPTION] = e
                    for cb in self._catch_block:
                        if cb.execute(context):
                            caught = True
                            break
                    if not caught:
                        raise
                finally:
                    context[constants.CTX_CURRENT_EXCEPTION] = None
            else:
                raise
        else:
            if self._else_block:
                self._else_block.execute(context)
        finally:
            if self._finally_block:
                self._finally_block.execute(context)


class RethrowMacro(expressions.DslExpression):
    def __init__(self, Rethrow):
        pass

    def execute(self, context):
        exception = context['$?currentException']
        if not exception:
            raise TypeError('Rethrow must be inside Catch')
        raise exception

    def __str__(self):
        return 'Rethrow'


def register():
    expressions.register_macro(ThrowMacro)
    expressions.register_macro(TryBlockMacro)
    expressions.register_macro(RethrowMacro)
