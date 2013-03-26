import datetime
import glob
import sys
import traceback

from conductor.openstack.common import service
from workflow import Workflow
from commands.dispatcher import CommandDispatcher
from config import Config
import reporting
import rabbitmq

import windows_agent
import cloud_formation

config = Config(sys.argv[1] if len(sys.argv) > 1 else None)


def task_received(task, message_id):
    with rabbitmq.RmqClient() as rmqclient:
        print 'Starting at', datetime.datetime.now()
        reporter = reporting.Reporter(rmqclient, message_id, task['id'])

        command_dispatcher = CommandDispatcher(
            task['id'], rmqclient, task['token'])
        workflows = []
        for path in glob.glob("data/workflows/*.xml"):
            print "loading", path
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
                traceback.print_exc()
                break

        command_dispatcher.close()

        del task['token']
        result_msg = rabbitmq.Message()
        result_msg.body = task
        result_msg.id = message_id

        rmqclient.send(message=result_msg, key='task-results')
        print 'Finished at', datetime.datetime.now()


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
                    rmq.declare('tasks2', 'tasks2')
                    rmq.declare('task-results', 'tasks2')
                    with rmq.open('tasks2') as subscription:
                        while True:
                            msg = subscription.get_message()
                            self.tg.add_thread(
                                task_received, msg.body, msg.id)
            except Exception as ex:
                print ex

