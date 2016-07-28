#    Copyright (c) 2016 Mirantis, Inc.
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

from oslo_log import log as logging
from yaql.language import specs
from yaql.language import yaqltypes

from murano.dsl import dsl
from murano.dsl import helpers

LOG = logging.getLogger(__name__)


@dsl.name('io.murano.system.GC')
class GarbageCollector(object):

    @staticmethod
    @specs.parameter('target', dsl.MuranoObjectParameter())
    @specs.parameter('handler', yaqltypes.String(nullable=True))
    def subscribe_destruction(target, handler=None):
        caller_context = helpers.get_caller_context()
        target_this = target.object
        receiver = helpers.get_this(caller_context)

        if handler:
            receiver.type.find_single_method(handler)

        dependency = {'subscriber': receiver.object_id,
                      'handler': handler}
        target_this.dependencies.setdefault(
            'onDestruction', []).append(dependency)

    @staticmethod
    @specs.parameter('target', dsl.MuranoObjectParameter())
    @specs.parameter('handler', yaqltypes.String(nullable=True))
    def unsubscibe_destruction(target, handler=None):
        caller_context = helpers.get_caller_context()
        target_this = target.object
        receiver = helpers.get_this(caller_context)

        if handler:
            receiver.type.find_single_method(handler)

        dependency = {'subscriber': receiver.object_id,
                      'handler': handler}
        dds = target_this.dependencies.get('onDestruction', [])
        if dependency in dds:
            dds.remove(dependency)
