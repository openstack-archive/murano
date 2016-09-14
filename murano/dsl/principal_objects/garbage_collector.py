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

from yaql.language import specs
from yaql.language import yaqltypes

from murano.dsl import dsl
from murano.dsl import helpers


@dsl.name('io.murano.system.GC')
class GarbageCollector(object):
    @staticmethod
    @specs.parameter('publisher', dsl.MuranoObjectParameter(decorate=False))
    @specs.parameter('subscriber', dsl.MuranoObjectParameter(decorate=False))
    @specs.parameter('handler', yaqltypes.String(nullable=True))
    def subscribe_destruction(publisher, subscriber, handler=None):
        publisher_this = publisher.real_this
        subscriber_this = subscriber.real_this

        if handler:
            subscriber.type.find_single_method(handler)

        dependency = GarbageCollector._find_dependency(
            publisher_this, subscriber_this, handler)

        if not dependency:
            dependency = {'subscriber': helpers.weak_ref(subscriber_this),
                          'handler': handler}
            publisher_this.destruction_dependencies.append(dependency)

    @staticmethod
    @specs.parameter('publisher', dsl.MuranoObjectParameter(decorate=False))
    @specs.parameter('subscriber', dsl.MuranoObjectParameter(decorate=False))
    @specs.parameter('handler', yaqltypes.String(nullable=True))
    def unsubscribe_destruction(publisher, subscriber, handler=None):
        publisher_this = publisher.real_this
        subscriber_this = subscriber.real_this

        if handler:
            subscriber.type.find_single_method(handler)

        dds = publisher_this.destruction_dependencies
        dependency = GarbageCollector._find_dependency(
            publisher_this, subscriber_this, handler)

        if dependency:
            dds.remove(dependency)

    @staticmethod
    def _find_dependency(publisher, subscriber, handler):
        dds = publisher.destruction_dependencies
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

    @staticmethod
    @specs.parameter('object_', dsl.MuranoObjectParameter(decorate=False))
    def is_doomed(object_):
        return helpers.get_object_store().is_doomed(object_)

    @staticmethod
    @specs.parameter('object_', dsl.MuranoObjectParameter(decorate=False))
    def is_destroyed(object_):
        return object_.destroyed
