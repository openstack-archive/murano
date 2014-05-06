# Copyright (c) 2014 Mirantis Inc.
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
from muranoapi.engine import package_class_loader
from muranoapi.engine import package_loader
from muranoapi.engine.system import status_reporter
import muranoapi.engine.system.system_objects as system_objects
from muranoapi.openstack.common.gettextutils import _  # noqa
from muranoapi.openstack.common import log as logging

RPC_SERVICE = None

LOG = logging.getLogger(__name__)


class TaskProcessingEndpoint(object):
    @staticmethod
    def handle_task(context, task):
        s_task = token_sanitizer.TokenSanitizer().sanitize(task)
        LOG.info(_('Starting processing task: {task_desc}').format(
            task_desc=anyjson.dumps(s_task)))

        env = environment.Environment()
        env.token = task['token']
        env.tenant_id = task['tenant_id']
        LOG.debug('Processing new task: {0}'.format(task))
        try:
            with package_loader.ApiPackageLoader(env.token, env.tenant_id) as \
                    pkg_loader:
                class_loader = package_class_loader.PackageClassLoader(
                    pkg_loader)
                system_objects.register(class_loader, pkg_loader)

                exc = executor.MuranoDslExecutor(class_loader, env)
                obj = exc.load(task['model'])

                try:
                    if obj is not None:
                        obj.type.invoke('deploy', exc, obj, {})
                except Exception as e:
                    reporter = status_reporter.StatusReporter()
                    reporter.initialize(obj)
                    reporter.report_error(obj, '{0}'.format(e))
                finally:
                    s_res = results_serializer.serialize(obj, exc)
                    rpc.api().process_result(s_res)
        except Exception as e:
            # TODO(gokrokve) report error here
            # TODO(slagun) code below needs complete rewrite and redesign
            LOG.exception("Error during task execution for tenant %s",
                          env.tenant_id)
            msg_env = Environment(task['model']['Objects']['?']['id'])
            reporter = status_reporter.StatusReporter()
            reporter.initialize(msg_env)
            reporter.report_error(msg_env, '{0}'.format(e))
            rpc.api().process_result(task['model'])


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


class Environment:
    def __init__(self, object_id):
        self.object_id = object_id
