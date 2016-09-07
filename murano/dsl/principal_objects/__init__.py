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

from murano.dsl.principal_objects import exception
from murano.dsl.principal_objects import garbage_collector
from murano.dsl.principal_objects import stack_trace
from murano.dsl.principal_objects import sys_object


def register(package):
    package.register_class(sys_object.SysObject)
    package.register_class(stack_trace.StackTrace)
    package.register_class(exception.DslException)
    package.register_class(garbage_collector.GarbageCollector)
