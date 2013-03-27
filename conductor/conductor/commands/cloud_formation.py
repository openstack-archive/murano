import anyjson
import eventlet

from conductor.openstack.common import log as logging
import conductor.helpers
from command import CommandBase
import conductor.config
from heatclient.client import Client
import heatclient.exc
import types

log = logging.getLogger(__name__)


class HeatExecutor(CommandBase):
    def __init__(self, stack, token):
        self._update_pending_list = []
        self._delete_pending_list = []
        self._stack = 'e' + stack
        settings = conductor.config.CONF.heat
        self._heat_client = Client('1', settings.url,
            token_only=True, token=token)

    def execute(self, command, callback, **kwargs):
        log.debug('Got command {0} on stack {1}'.format(command, self._stack))

        if command == 'CreateOrUpdate':
            return self._execute_create_update(
                kwargs['template'],
                kwargs['mappings'],
                kwargs['arguments'],
                callback)
        elif command == 'Delete':
            return self._execute_delete(callback)


    def _execute_create_update(self, template, mappings, arguments, callback):
        with open('data/templates/cf/%s.template' % template) as template_file:
            template_data = template_file.read()

        template_data = conductor.helpers.transform_json(
            anyjson.loads(template_data), mappings)

        self._update_pending_list.append({
            'template': template_data,
            'arguments': arguments,
            'callback': callback
        })

    def _execute_delete(self, callback):
        self._delete_pending_list.append({
            'callback': callback
        })


    def has_pending_commands(self):
        return len(self._update_pending_list) + \
               len(self._delete_pending_list) > 0

    def execute_pending(self):
        r1 = self._execute_pending_updates()
        r2 = self._execute_pending_deletes()
        return r1 or r2

    def _execute_pending_updates(self):
        if not len(self._update_pending_list):
            return False

        template = {}
        arguments = {}
        for t in self._update_pending_list:
            template = conductor.helpers.merge_dicts(
                template, t['template'], max_levels=2)
            arguments = conductor.helpers.merge_dicts(
                arguments, t['arguments'], max_levels=1)

        log.info('Executing heat template {0} with arguments {1} on stack {2}'
            .format(anyjson.dumps(template), arguments, self._stack))

        try:
            self._heat_client.stacks.update(
                stack_id=self._stack,
                parameters=arguments,
                template=template)
            log.debug('Waiting for the stack {0} to be update'
                .format(self._stack))
            self._wait_state('UPDATE_COMPLETE')
            log.info('Stack {0} updated'.format(self._stack))
        except heatclient.exc.HTTPNotFound:
            self._heat_client.stacks.create(
                stack_name=self._stack,
                parameters=arguments,
                template=template)
            log.debug('Waiting for the stack {0} to be create'
                .format(self._stack))
            self._wait_state('CREATE_COMPLETE')
            log.info('Stack {0} created'.format(self._stack))


        pending_list = self._update_pending_list
        self._update_pending_list = []

        for item in pending_list:
            item['callback'](True)

        return True

    def _execute_pending_deletes(self):
        if not len(self._delete_pending_list):
            return False

        log.debug('Deleting stack {0}'.format(self._stack))
        try:
            self._heat_client.stacks.delete(
                stack_id=self._stack)
            log.debug('Waiting for the stack {0} to be deleted'
                .format(self._stack))
            self._wait_state(['DELETE_COMPLETE', ''])
            log.info('Stack {0} deleted'.format(self._stack))
        except Exception as ex:
            log.exception(ex)

        pending_list = self._delete_pending_list
        self._delete_pending_list = []

        for item in pending_list:
            item['callback'](True)
        return True

    def _wait_state(self, state):
        if isinstance(state, types.ListType):
            states = state
        else:
            states = [state]


        while True:
            try:
                status = self._heat_client.stacks.get(
                    stack_id=self._stack).stack_status
            except heatclient.exc.HTTPNotFound:
                status = ''

            if 'IN_PROGRESS' in status:
                eventlet.sleep(1)
                continue
            if status not in states:
                raise EnvironmentError()
            return

