import datetime
import glob
import json
import sys

from conductor.openstack.common import service
from workflow import Workflow
import cloud_formation
import windows_agent
from commands.dispatcher import CommandDispatcher
from config import Config
import reporting
import rabbitmq

config = Config(sys.argv[1] if len(sys.argv) > 1 else None)

def task_received(task, message_id):
    with rabbitmq.RmqClient() as rmqclient:
        print 'Starting at', datetime.datetime.now()
        reporter = reporting.Reporter(rmqclient, message_id, task['id'])

        command_dispatcher = CommandDispatcher(task['name'], rmqclient)
        workflows = []
        for path in glob.glob("data/workflows/*.xml"):
            print "loading", path
            workflow = Workflow(path, task, command_dispatcher, config, reporter)
            workflows.append(workflow)

        while True:
            for workflow in workflows:
                workflow.execute()
            if not command_dispatcher.execute_pending():
                break

        command_dispatcher.close()
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
                    rmq.declare('tasks', 'tasks')
                    rmq.declare('task-results', 'tasks')
                    with rmq.open('tasks') as subscription:
                        while True:
                            msg = subscription.get_message()
                            self.tg.add_thread(
                                task_received, msg.body, msg.id)
            except Exception as ex:
                print ex

