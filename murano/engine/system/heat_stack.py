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

import copy

import eventlet
import heatclient.client as hclient
import heatclient.exc as heat_exc
import keystoneclient.v2_0.client as ksclient

import murano.common.config as config
import murano.common.utils as utils
import murano.dsl.helpers as helpers
import murano.dsl.murano_class as murano_class
import murano.dsl.murano_object as murano_object
import murano.openstack.common.log as logging

LOG = logging.getLogger(__name__)

HEAT_TEMPLATE_VERSION = '2013-05-23'


class HeatStackError(Exception):
    pass


@murano_class.classname('io.murano.system.HeatStack')
class HeatStack(murano_object.MuranoObject):
    def initialize(self, _context, name, description=None):
        self._name = name
        self._template = None
        self._parameters = {}
        self._applied = True
        self._description = description
        environment = helpers.get_environment(_context)
        keystone_settings = config.CONF.keystone
        heat_settings = config.CONF.heat

        client = ksclient.Client(
            endpoint=keystone_settings.auth_url,
            cacert=keystone_settings.ca_file or None,
            cert=keystone_settings.cert_file or None,
            key=keystone_settings.key_file or None,
            insecure=keystone_settings.insecure)

        if not client.authenticate(
                auth_url=keystone_settings.auth_url,
                tenant_id=environment.tenant_id,
                token=environment.token):
            raise heat_exc.HTTPUnauthorized()

        heat_url = client.service_catalog.url_for(
            service_type='orchestration',
            endpoint_type=heat_settings.endpoint_type)

        self._heat_client = hclient.Client(
            '1',
            heat_url,
            username='badusername',
            password='badpassword',
            token_only=True,
            token=client.auth_token,
            ca_file=heat_settings.ca_file or None,
            cert_file=heat_settings.cert_file or None,
            key_file=heat_settings.key_file or None,
            insecure=heat_settings.insecure)

    def current(self):
        if self._template is not None:
            return self._template
        try:
            stack_info = self._heat_client.stacks.get(stack_id=self._name)
            template = self._heat_client.stacks.template(
                stack_id='{0}/{1}'.format(
                    stack_info.stack_name,
                    stack_info.id))
            # template = {}
            self._template = template
            self._parameters.update(
                HeatStack._remove_system_params(stack_info.parameters))
            self._applied = True
            return self._template.copy()
        except heat_exc.HTTPNotFound:
            self._applied = True
            self._template = {}
            self._parameters.clear()
            return {}

    def parameters(self):
        self.current()
        return self._parameters.copy()

    def reload(self):
        self._template = None
        self._parameters.clear()
        return self.current()

    def setTemplate(self, template):
        self._template = template
        self._parameters.clear()
        self._applied = False

    def setParameters(self, parameters):
        self._parameters = parameters
        self._applied = False

    def updateTemplate(self, template):
        template_version = template.get('heat_template_version',
                                        HEAT_TEMPLATE_VERSION)
        if template_version != HEAT_TEMPLATE_VERSION:
            err_msg = ("Currently only heat_template_version %s "
                       "is supported." % HEAT_TEMPLATE_VERSION)
            raise HeatStackError(err_msg)
        self.current()
        self._template = helpers.merge_dicts(self._template, template)
        self._applied = False

    @staticmethod
    def _remove_system_params(parameters):
        return dict((k, v) for k, v in parameters.iteritems() if
                    not k.startswith('OS::'))

    def _get_status(self):
        status = [None]

        def status_func(state_value):
            status[0] = state_value
            return True

        self._wait_state(status_func)
        return status[0]

    def _wait_state(self, status_func):
        tries = 4
        delay = 1
        while tries > 0:
            while True:
                try:
                    stack_info = self._heat_client.stacks.get(
                        stack_id=self._name)
                    status = stack_info.stack_status
                    tries = 4
                    delay = 1
                except heat_exc.HTTPNotFound:
                    stack_info = None
                    status = 'NOT_FOUND'
                except Exception:
                    tries -= 1
                    delay *= 2
                    if not tries:
                        raise
                    eventlet.sleep(delay)
                    break

                if 'IN_PROGRESS' in status:
                    eventlet.sleep(2)
                    continue
                if not status_func(status):
                    reason = ': {0}'.format(
                        stack_info.stack_status_reason) if stack_info else ''
                    raise EnvironmentError(
                        "Unexpected stack state {0}{1}".format(status, reason))

                try:
                    return dict([(t['output_key'], t['output_value'])
                                 for t in stack_info.outputs])
                except Exception:
                    return {}
        return {}

    def output(self):
        return self._wait_state(lambda status: True)

    def push(self):
        if self._applied or self._template is None:
            return

        if 'heat_template_version' not in self._template:
            self._template['heat_template_version'] = HEAT_TEMPLATE_VERSION

        if 'description' not in self._template and self._description:
            self._template['description'] = self._description

        template = copy.deepcopy(self._template)
        LOG.info('Pushing: {0}'.format(template))

        current_status = self._get_status()
        resources = template.get('Resources') or template.get('resources')
        if current_status == 'NOT_FOUND':
            if resources:
                self._heat_client.stacks.create(
                    stack_name=self._name,
                    parameters=self._parameters,
                    template=template,
                    disable_rollback=True)

                self._wait_state(
                    lambda status: status == 'CREATE_COMPLETE')
        else:
            if resources:
                self._heat_client.stacks.update(
                    stack_id=self._name,
                    parameters=self._parameters,
                    template=template)
                self._wait_state(
                    lambda status: status == 'UPDATE_COMPLETE')
            else:
                self.delete()

        self._applied = not utils.is_different(self._template, template)

    def delete(self):
        try:
            if not self.current():
                return
            self._heat_client.stacks.delete(
                stack_id=self._name)
            self._wait_state(
                lambda status: status in ('DELETE_COMPLETE', 'NOT_FOUND'))
        except heat_exc.NotFound:
            LOG.warn("Stack {0} already deleted?".format(self._name))

        self._template = {}
        self._applied = True
