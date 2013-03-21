import anyjson
import os
import uuid

import conductor.helpers
from command import CommandBase
from subprocess import call


class HeatExecutor(CommandBase):
    def __init__(self, stack):
        self._pending_list = []
        self._stack = stack

    def execute(self, template, mappings, arguments, callback):
        with open('data/templates/cf/%s.template' % template) as template_file:
            template_data = template_file.read()

        template_data = conductor.helpers.transform_json(
            anyjson.loads(template_data), mappings)

        self._pending_list.append({
            'template': template_data,
            'arguments': arguments,
            'callback': callback
        })

    def has_pending_commands(self):
        return len(self._pending_list) > 0

    def execute_pending(self):
        if not self.has_pending_commands():
            return False

        template = {}
        arguments = {}
        for t in self._pending_list:
            template = conductor.helpers.merge_dicts(
                template, t['template'], max_levels=2)
            arguments = conductor.helpers.merge_dicts(
                arguments, t['arguments'], max_levels=1)

        print 'Executing heat template', anyjson.dumps(template), \
            'with arguments', arguments, 'on stack', self._stack

        if not os.path.exists("tmp"):
            os.mkdir("tmp")
        file_name = "tmp/" + str(uuid.uuid4())
        print "Saving template to", file_name
        with open(file_name, "w") as f:
            f.write(anyjson.dumps(template))

        arguments_str = ';'.join(['%s=%s' % (key, value)
                                  for (key, value) in arguments.items()])
        # call([
        #     "./heat_run", "stack-create",
        #     "-f" + file_name,
        #     "-P" + arguments_str,
        #     self._stack
        # ])

        pending_list = self._pending_list
        self._pending_list = []

        for item in pending_list:
            item['callback'](True)



        return True
