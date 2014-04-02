# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid

import anyjson
from oslo import messaging
from oslo.messaging import target

from muranoapi.common import config
from muranoapi.common.helpers import token_sanitizer
from muranoapi.common import rpc
from muranoapi.dsl import executor
from muranoapi.dsl import results_serializer
from muranoapi.engine import environment
from muranoapi.engine import simple_cloader
import muranoapi.engine.system.system_objects as system_objects
from muranoapi.openstack.common.gettextutils import _  # noqa
from muranoapi.openstack.common import log as logging

RPC_SERVICE = None

log = logging.getLogger(__name__)


class TaskProcessingEndpoint(object):
    @staticmethod
    def handle_task(context, task):
        s_task = token_sanitizer.TokenSanitizer().sanitize(task)
        log.info('Starting processing task: {0}'.format(anyjson.dumps(s_task)))

        env = environment.Environment()
        env.token = task['token']
        env.tenant_id = task['tenant_id']

        cl = simple_cloader.SimpleClassLoader(config.CONF.metadata_dir)
        system_objects.register(cl, config.CONF.metadata_dir)

        exc = executor.MuranoDslExecutor(cl, env)
        obj = exc.load(task['model'])

        obj.type.invoke('deploy', exc, obj, {})

        s_res = results_serializer.serialize(obj, exc)
        rpc.api().process_result(s_res)


def _prepare_rpc_service(server_id):
    endpoints = [TaskProcessingEndpoint()]

    transport = messaging.get_transport(config.CONF)
    s_target = target.Target('murano', 'tasks', server=server_id)
    return messaging.get_rpc_server(transport, s_target, endpoints, 'eventlet')


def get_rpc_service():
    global RPC_SERVICE

    if RPC_SERVICE is None:
        RPC_SERVICE = _prepare_rpc_service(str(uuid.uuid4()))
    return RPC_SERVICE
