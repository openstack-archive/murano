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

import datetime
import glob
import sys
import traceback

import anyjson
from conductor.openstack.common import service
from workflow import Workflow
from commands.dispatcher import CommandDispatcher
from openstack.common import log as logging
from config import Config
import reporting
import rabbitmq

import windows_agent
import cloud_formation

config = Config(sys.argv[1] if len(sys.argv) > 1 else None)

log = logging.getLogger(__name__)


def task_received(task, message_id):
    with rabbitmq.RmqClient() as rmqclient:
        try:
            log.info('Starting processing task {0}: {1}'.format(
                message_id, anyjson.dumps(task)))
            reporter = reporting.Reporter(rmqclient, message_id, task['id'])

            command_dispatcher = CommandDispatcher(
                task['name'], rmqclient, task['token'], task['tenant_id'])
            workflows = []
            for path in glob.glob("data/workflows/*.xml"):
                log.debug('Loading XML {0}'.format(path))
                workflow = Workflow(path, task, command_dispatcher, config,
                                    reporter)
                workflows.append(workflow)

            while True:
                try:
                    while True:
                        result = False
                        for workflow in workflows:
                            if workflow.execute():
                                result = True
                        if not result:
                            break
                    if not command_dispatcher.execute_pending():
                        break
                except Exception as ex:
                    log.exception(ex)
                    break

            command_dispatcher.close()
        finally:
            del task['token']
            result_msg = rabbitmq.Message()
            result_msg.body = task
            result_msg.id = message_id

            rmqclient.send(message=result_msg, key='task-results')
    log.info('Finished processing task {0}. Result = {1}'.format(
        message_id, anyjson.dumps(task)))


class ConductorWorkflowService(service.Service):
    def __init__(self):
        super(ConductorWorkflowService, self).__init__()

    def start(self):
        super(ConductorWorkflowService, self).start()
        self.tg.add_thread(self._start_rabbitmq)

    def stop(self):
        super(ConductorWorkflowService, self).stop()

    def _start_rabbitmq(self):
        while True:
            try:
                with rabbitmq.RmqClient() as rmq:
                    rmq.declare('tasks', 'tasks')
                    rmq.declare('task-results')
                    with rmq.open('tasks') as subscription:
                        while True:
                            msg = subscription.get_message()
                            self.tg.add_thread(
                                task_received, msg.body, msg.id)
            except Exception as ex:
                log.exception(ex)

