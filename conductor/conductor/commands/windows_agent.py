import json
import uuid

from conductor.openstack.common import log as logging
from conductor.rabbitmq import Message
import conductor.helpers
from command import CommandBase

log = logging.getLogger(__name__)


class WindowsAgentExecutor(CommandBase):
    def __init__(self, stack, rmqclient):
        self._stack = stack
        self._rmqclient = rmqclient
        self._pending_list = []
        self._results_queue = '-execution-results-%s' % str(stack).lower()
        rmqclient.declare(self._results_queue)

    def execute(self, template, mappings, host, service, callback):
        with open('data/templates/agent/%s.template' % template) as file:
            template_data = file.read()

        template_data = conductor.helpers.transform_json(
            json.loads(template_data), mappings)

        id = str(uuid.uuid4()).lower()
        host = ('%s-%s-%s' % (self._stack, service, host)).lower()
        self._pending_list.append({
            'id': id,
            'callback': callback
        })

        msg = Message()
        msg.body = template_data
        msg.id = id
        self._rmqclient.declare(host)
        self._rmqclient.send(message=msg, key=host)
        log.info('Sending RMQ message {0} to {1} with id {2}'.format(
            template_data, host, id))

    def has_pending_commands(self):
        return len(self._pending_list) > 0

    def execute_pending(self):
        if not self.has_pending_commands():
            return False

        with self._rmqclient.open(self._results_queue) as subscription:
            while self.has_pending_commands():
                msg = subscription.get_message()
                msg_id = msg.id.lower()
                item, index = conductor.helpers.find(
                    lambda t: t['id'] == msg_id, self._pending_list)
                if item:
                    self._pending_list.pop(index)
                    item['callback'](msg.body)

        return True


