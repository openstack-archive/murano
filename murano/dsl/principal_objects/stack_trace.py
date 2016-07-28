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

import inspect
import os.path

import six
from yaql import specs

from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import helpers
from murano.dsl import yaql_integration


@dsl.name('io.murano.StackTrace')
class StackTrace(object):
    def __init__(self, this, context, include_native_frames=True):
        frames = []
        caller_context = context
        while True:
            if not caller_context:
                break
            frame = compose_stack_frame(caller_context)
            frames.append(frame)
            caller_context = helpers.get_caller_context(caller_context)
        frames.reverse()
        frames.pop()

        if include_native_frames:
            native_frames = []
            for frame in inspect.trace()[1:]:
                location = dsl_types.ExpressionFilePosition(
                    os.path.abspath(frame[1]), frame[2],
                    -1, frame[2], -1)
                method = frame[3]
                native_frames.append({
                    'instruction': frame[4][0].strip(),
                    'location': location,
                    'methodName': method,
                    'typeName': None
                })
            frames.extend(native_frames)

        this.properties.frames = frames

    @specs.meta(constants.META_NO_TRACE, True)
    @specs.meta('Usage', 'Action')
    def to_string(self, this, prefix=''):
        return '\n'.join([format_frame(t, prefix)for t in this['frames']])


def compose_stack_frame(context):
    instruction = helpers.get_current_instruction(context)
    method = helpers.get_current_method(context)
    return {
        'instruction': None if instruction is None
        else six.text_type(instruction),

        'location': None if instruction is None
        else instruction.source_file_position,

        'methodName': None if method is None else method.name,
        'typeName': None if method is None else method.declaring_type.name
    }


def format_frame(frame, prefix=''):
    instruction = frame['instruction']
    method_name = frame['methodName']
    type_name = frame['typeName']
    location = frame['location']
    if type_name:
        method_name += ' of type ' + type_name

    if location:
        args = (
            os.path.abspath(location.file_path),
            location.start_line,
            ':' + str(location.start_column)
            if location.start_column >= 0 else '',
            method_name,
            instruction,
            prefix
        )
        return (u'{5}File "{0}", line {1}{2} in method {3}\n'
                u'{5}    {4}').format(*args)
    else:
        return u'{2}File <unknown> in method {0}\n{2}    {1}'.format(
            method_name, instruction, prefix)


def create_stack_trace(context, include_native_frames=True):
        stacktrace = yaql_integration.call_func(
            context, 'new', 'io.murano.StackTrace',
            includeNativeFrames=include_native_frames)
        return dsl.MuranoObjectInterface.create(stacktrace)
