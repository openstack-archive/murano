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

import os.path

import yaql.context

import murano.dsl.helpers as helpers


@yaql.context.ContextAware()
def stack_trace(context):
    frames = []
    while True:
        context = helpers.get_caller_context(context)
        if not context:
            break
        instruction = helpers.get_current_instruction(context)
        frames.append({
            'instruction': None if instruction is None else str(instruction),
            'location': None if instruction is None
            else instruction.file_position,
            'method': helpers.get_current_method(context),
            'class': helpers.get_type(context)
        })
    frames.pop()
    return frames


def format_stack_trace_yaql(trace):
    return format_stack_trace(trace, '')


def format_stack_trace(trace, prefix=''):
    def format_frame(frame):
        instruction = frame['instruction']
        method = frame['method']
        murano_class = frame['class']
        location = frame['location']

        if location:
            return '{5}File "{0}" at {1}:{2} in method {3} of class {6}\n' \
                   '{5}    {4}'.format(
                       os.path.abspath(location.file_path),
                       location.start_line,
                       location.start_column,
                       method,
                       instruction,
                       prefix,
                       murano_class.name)
        else:
            return '{2}File <unknown> in method {0}\n{2}    {1}'.format(
                method, instruction, prefix)

    return '\n'.join([format_frame(t)for t in trace()])
