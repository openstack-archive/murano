import json
import uuid

import conductor.helpers
from command import CommandBase


class WindowsAgentExecutor(CommandBase):
    def __init__(self, stack, rmqclient):
        self._stack = stack
        self._rmqclient = rmqclient
        self._callback = None
        self._pending_list = []
        self._current_pending_list = []
        rmqclient.subscribe('-execution-results', self._on_message)

    def execute(self, template, mappings, host, callback):
        with open('data/templates/agent/%s.template' %
                  template) as template_file:
            template_data = template_file.read()

        template_data = json.dumps(conductor.helpers.transform_json(
            json.loads(template_data), mappings))

        self._pending_list.append({
            'id': str(uuid.uuid4()).lower(),
            'template': template_data,
            'host': ('%s-%s' % (self._stack, host)).lower().replace(' ', '-'),
            'callback': callback
        })

    def _on_message(self, body, message_id, **kwargs):
        msg_id = message_id.lower()
        item, index = conductor.helpers.find(lambda t: t['id'] == msg_id,
                                             self._current_pending_list)
        if item:
            self._current_pending_list.pop(index)
            item['callback'](json.loads(body))
            if self._callback and not self._current_pending_list:
                cb = self._callback
                self._callback = None
                cb()

    def has_pending_commands(self):
        return len(self._pending_list) > 0

    def execute_pending(self, callback):
        if not self.has_pending_commands():
            return False

        self._current_pending_list = self._pending_list
        self._pending_list = []

        self._callback = callback

        for rec in self._current_pending_list:
            self._rmqclient.send(
                queue=rec['host'], data=rec['template'], message_id=rec['id'])
            print 'Sending RMQ message %s to %s' % (
                rec['template'], rec['host'])

        return True

    def close(self):
        self._rmqclient.unsubscribe('-execution-results')

