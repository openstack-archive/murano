import json

import conductor.helpers
from command import CommandBase

class WindowsAgentExecutor(CommandBase):
    def __init__(self, stack, rmqclient):
        self._pending_list = []
        self._stack = stack
        self._rmqclient = rmqclient
        self._callback = None
        rmqclient.subscribe('-execution-results', self._on_message)
        print "--------------------"

    def execute(self, template, mappings, host, callback):
        with open('data/templates/agent/%s.template' % template) as template_file:
            template_data = template_file.read()

        template_data = json.dumps(conductor.helpers.transform_json(json.loads(template_data), mappings))

        self._pending_list.append({
            'template': template_data,
            'host': ('%s-%s' % (self._stack, host)).lower().replace(' ', '-'),
            'callback': callback
        })

    def _on_message(self, body):
        if self._pending_list:
            item = self._pending_list.pop()
            item['callback'](json.loads(body))
            if self._callback and not self._pending_list:
                cb = self._callback
                self._callback = None
                cb()

    def has_pending_commands(self):
        return len(self._pending_list) > 0

    def execute_pending(self, callback):
        if not self._pending_list:
            return False

        self._callback = callback

        for t in self._pending_list:
            self._rmqclient.send(queue=t['host'], data=t['template'])
            print 'Sending RMQ message %s to %s' % (t['template'], t['host'])

        callbacks = []
        for t in self._pending_list:
            if t['callback']:
                callbacks.append(t['callback'])

        return True

    def close(self):
        self._rmqclient.unsubscribe('-execution-results')

