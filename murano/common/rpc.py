#    Copyright (c) 2013 Mirantis, Inc.
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

from oslo_config import cfg
import oslo_messaging as messaging
from oslo_messaging.rpc import dispatcher
from oslo_messaging import target

CONF = cfg.CONF

NOTIFICATION_TRANSPORT = None
TRANSPORT = None


def init():
    global TRANSPORT, NOTIFICATION_TRANSPORT
    TRANSPORT = messaging.get_rpc_transport(CONF)
    NOTIFICATION_TRANSPORT = messaging.get_notification_transport(CONF)


def initialized():
    return None not in [TRANSPORT, NOTIFICATION_TRANSPORT]


def cleanup():
    global TRANSPORT, NOTIFICATION_TRANSPORT
    if TRANSPORT is not None:
        TRANSPORT.cleanup()
    if NOTIFICATION_TRANSPORT is not None:
        NOTIFICATION_TRANSPORT.cleanup()
    TRANSPORT = NOTIFICATION_TRANSPORT = None


def get_client(target, timeout=None):
    if TRANSPORT is None:
        init()
    return messaging.RPCClient(
        TRANSPORT,
        target,
        timeout=timeout
    )


def get_server(target, endpoints, executor):
    if TRANSPORT is None:
        init()
    access_policy = dispatcher.DefaultRPCAccessPolicy
    return messaging.get_rpc_server(
        TRANSPORT,
        target,
        endpoints,
        executor=executor,
        access_policy=access_policy
    )


def get_notification_listener(targets, endpoints, executor):
    if NOTIFICATION_TRANSPORT is None:
        init()
    return messaging.get_notification_listener(
        NOTIFICATION_TRANSPORT,
        targets,
        endpoints,
        executor=executor
    )


class ApiClient(object):
    def __init__(self):
        client_target = target.Target('murano', 'results')
        self._client = get_client(client_target, timeout=15)

    def process_result(self, result, environment_id):
        return self._client.call({}, 'process_result', result=result,
                                 environment_id=environment_id)


class EngineClient(object):
    def __init__(self):
        client_target = target.Target('murano', 'tasks')
        self._client = get_client(client_target, timeout=15)

    def handle_task(self, task):
        return self._client.cast({}, 'handle_task', task=task)

    def call_static_action(self, task):
        return self._client.call({}, 'call_static_action', task=task)

    def generate_schema(self, credentials, class_name, method_names=None,
                        class_version=None, package_name=None):
        return self._client.call(
            credentials, 'generate_schema',
            class_name=class_name,
            method_names=method_names,
            class_version=class_version,
            package_name=package_name
        )


def api():
    if not initialized():
        init()
    return ApiClient()


def engine():
    if not initialized():
        init()
    return EngineClient()
