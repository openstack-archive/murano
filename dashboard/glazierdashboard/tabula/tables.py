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

import logging
import re

from django.utils.translation import ugettext_lazy as _
from horizon import messages
from horizon import tables
from glazierdashboard.tabula import api


LOG = logging.getLogger(__name__)


class CreateService(tables.LinkAction):
    name = 'CreateService'
    verbose_name = _('Create Service')
    url = 'horizon:project:tabula:create'
    classes = ('btn-launch', 'ajax-modal')

    def allowed(self, request, datum):
        return True

    def action(self, request, service):
        api.service_create(request, service)


class CreateEnvironment(tables.LinkAction):
    name = 'CreateEnvironment'
    verbose_name = _('Create Environment')
    url = 'horizon:project:tabula:create_dc'
    classes = ('btn-launch', 'ajax-modal')

    def allowed(self, request, datum):
        return True

    def action(self, request, environment):
        api.environment_create(request, environment)


class DeleteEnvironment(tables.BatchAction):
    name = 'delete'
    action_present = _('Delete')
    action_past = _('Delete')
    data_type_singular = _('Environment')
    data_type_plural = _('Environment')
    classes = ('btn-danger', 'btn-terminate')

    def allowed(self, request, datum):
        return True

    def action(self, request, environment_id):
        api.environment_delete(request, environment_id)


class DeleteService(tables.BatchAction):
    name = 'delete'
    action_present = _('Delete')
    action_past = _('Delete')
    data_type_singular = _('Service')
    data_type_plural = _('Service')
    classes = ('btn-danger', 'btn-terminate')

    def allowed(self, request, datum):
        return True

    def action(self, request, service_id):
        link = request.__dict__['META']['HTTP_REFERER']
        datacenter_id = re.search('tabula/(\S+)', link).group(0)[7:-1]

        try:
            api.service_delete(request, datacenter_id, service_id)
        except:
            messages.error(request, _('Sorry, you can not delete this '
                                      'service right now.'))


class DeployEnvironment(tables.BatchAction):
    name = 'deploy'
    action_present = _('Deploy')
    action_past = _('Deploy')
    data_type_singular = _('Environment')
    data_type_plural = _('Environment')
    classes = 'btn-launch'

    def allowed(self, request, datum):
        return True

    def action(self, request, environment_id):
        return api.environment_deploy(request, environment_id)


class ShowEnvironmentServices(tables.LinkAction):
    name = 'edit'
    verbose_name = _('Services')
    url = 'horizon:project:tabula:services'

    def allowed(self, request, instance):
        return True


class UpdateEnvironmentRow(tables.Row):
    ajax = True

    def get_data(self, request, environment_id):
        return api.environment_get(request, environment_id)


class UpdateServiceRow(tables.Row):
    ajax = True

    def get_data(self, request, service_id):

        link = request.__dict__['META']['HTTP_REFERER']
        environment_id = re.search('tabula/(\S+)', link).group(0)[77:-1]

        service = api.service_get(request, environment_id, service_id)

        return service


STATUS_DISPLAY_CHOICES = (
    ('draft', 'Ready to deploy'),
    ('pending', 'Wait for configuration'),
    ('inprogress', 'Deploy in progress'),
    ('finished', 'Active')
)


class EnvironmentsTable(tables.DataTable):
    STATUS_CHOICES = (
        (None, True),
        ('Ready to deploy', True),
        ('Active', True)
    )

    name = tables.Column('name',
                         link=('horizon:project:tabula:services'),
                         verbose_name=_('Name'))

    status = tables.Column('status', verbose_name=_('Status'),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)

    class Meta:
        name = 'tabula'
        verbose_name = _('Environments')
        row_class = UpdateEnvironmentRow
        status_columns = ['status']
        table_actions = (CreateEnvironment,)
        row_actions = (ShowEnvironmentServices, DeleteEnvironment,
                       DeployEnvironment)


class ServicesTable(tables.DataTable):
    STATUS_CHOICES = (
        (None, True),
        ('Ready to deploy', True),
        ('Active', True)
    )

    name = tables.Column('name', verbose_name=_('Name'),
                         link=('horizon:project:tabula:service_details'))

    _type = tables.Column('service_type', verbose_name=_('Type'))

    status = tables.Column('status', verbose_name=_('Status'),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)

    operation = tables.Column('operation', verbose_name=_('Operation'))

    class Meta:
        name = 'services'
        verbose_name = _('Services')
        row_class = UpdateServiceRow
        status_columns = ['status']
        table_actions = (CreateService,)
