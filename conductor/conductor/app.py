import datetime
import glob
import json
import time
import sys
import tornado.ioloop

import rabbitmq
from workflow import Workflow
import cloud_formation
import windows_agent
from commands.dispatcher import CommandDispatcher
from config import Config
import reporting

config = Config(sys.argv[1] if len(sys.argv) > 1 else None)

rmqclient = rabbitmq.RabbitMqClient(
    virtual_host=config.get_setting('rabbitmq', 'vhost', '/'),
    login=config.get_setting('rabbitmq', 'login', 'guest'),
    password=config.get_setting('rabbitmq', 'password', 'guest'),
    host=config.get_setting('rabbitmq', 'host', 'localhost'))


def schedule(callback, *args, **kwargs):
    tornado.ioloop.IOLoop.instance().add_timeout(time.time() + 0.1,
        lambda args=args, kwargs=kwargs: callback(*args, **kwargs))


def task_received(task, message_id):
    print 'Starting at', datetime.datetime.now()
    reporter = reporting.Reporter(rmqclient, message_id, task['id'])

    command_dispatcher = CommandDispatcher(task['name'], rmqclient)
    workflows = []
    for path in glob.glob("data/workflows/*.xml"):
        print "loading", path
        workflow = Workflow(path, task, command_dispatcher, config, reporter)
        workflows.append(workflow)

    def loop(callback):
        for workflow in workflows:
            workflow.execute()
        func = lambda: schedule(loop, callback)
        if not command_dispatcher.execute_pending(func):
            callback()

    def shutdown():
        command_dispatcher.close()
        rmqclient.send('task-results', json.dumps(task),
                       message_id=message_id)
        print 'Finished at', datetime.datetime.now()

    loop(shutdown)


def message_received(body, message_id, **kwargs):
    task_received(json.loads(body), message_id)


def start():
    rmqclient.subscribe("tasks", message_received)

rmqclient.start(start)
tornado.ioloop.IOLoop.instance().start()
