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
        target_this = target.object.real_this
        receiver = helpers.get_this(caller_context)

        if handler:
            receiver.type.find_single_method(handler)

        dependency = GarbageCollector._find_dependency(
            target_this, receiver, handler)

        if not dependency:
            dependency = {'subscriber': helpers.weak_ref(receiver),
                          'handler': handler}
            target_this.dependencies.setdefault(
                'onDestruction', []).append(dependency)

    @staticmethod
    @specs.parameter('target', dsl.MuranoObjectParameter())
    @specs.parameter('handler', yaqltypes.String(nullable=True))
    def unsubscribe_destruction(target, handler=None):
        caller_context = helpers.get_caller_context()
        target_this = target.object.real_this
        receiver = helpers.get_this(caller_context)

        if handler:
            receiver.type.find_single_method(handler)

        dds = target_this.dependencies.get('onDestruction', [])
        dependency = GarbageCollector._find_dependency(
            target_this, receiver, handler)

        if dependency:
            dds.remove(dependency)

    @staticmethod
    def _find_dependency(target, subscriber, handler):
        dds = target.dependencies.get('onDestruction', [])
        for dd in dds:
            if dd['handler'] != handler:
                continue
            d_subscriber = dd['subscriber']
            if d_subscriber:
                d_subscriber = d_subscriber()
            if d_subscriber == subscriber:
                return dd

    @staticmethod
    def collect():
        helpers.get_executor().object_store.cleanup()
