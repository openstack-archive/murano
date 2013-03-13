# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


# TO DO: clear extra modules

import re
import logging

from django import shortcuts
from django import template
from django.core import urlresolvers
from django.template.defaultfilters import title
from django.utils.http import urlencode
from django.utils.translation import string_concat, ugettext_lazy as _

from horizon.conf import HORIZON_CONFIG
from horizon import exceptions
from horizon import messages
from horizon import tables
from horizon.templatetags import sizeformat
from horizon.utils.filters import replace_underscores

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.access_and_security \
        .floating_ips.workflows import IPAssociationWorkflow


LOG = logging.getLogger(__name__)


class CreateService(tables.LinkAction):
    name = 'CreateService'
    verbose_name = _('Create Service')
    url = 'horizon:project:windc:create'
    classes = ('btn-launch', 'ajax-modal')

    def allowed(self, request, datum):
        return True

    def action(self, request, service):
        api.windc.services_create(request, service)


class CreateDataCenter(tables.LinkAction):
    name = 'CreateDataCenter'
    verbose_name = _('Create Windows Data Center')
    url = 'horizon:project:windc:create_dc'
    classes = ('btn-launch', 'ajax-modal')

    def allowed(self, request, datum):
        return True

    def action(self, request, datacenter):
        api.windc.datacenters_create(request, datacenter)


class DeleteDataCenter(tables.BatchAction):
    name = 'delete'
    action_present = _('Delete')
    action_past = _('Delete')
    data_type_singular = _('Data Center')
    data_type_plural = _('Data Center')
    classes = ('btn-danger', 'btn-terminate')

    def allowed(self, request, datum):
        return True

    def action(self, request, datacenter_id):
        api.windc.datacenters_delete(request, datacenter_id)


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
        datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]

        try:
            api.windc.services_delete(request, datacenter_id, service_id)
        except:
            messages.error(request,
                  _('Sorry, you can not delete this service right now.'))


class DeployDataCenter(tables.BatchAction):
    name = 'deploy'
    action_present = _('Deploy')
    action_past = _('Deploy')
    data_type_singular = _('Data Center')
    data_type_plural = _('Data Center')
    classes = ('btn-launch')

    def allowed(self, request, datum):
        return True

    def action(self, request, datacenter_id):
        return api.windc.datacenters_deploy(request, datacenter_id)


class ShowDataCenterServices(tables.LinkAction):
    name = 'edit'
    verbose_name = _('Services')
    url = 'horizon:project:windc:services'

    def allowed(self, request, instance):
        return True


class UpdateDCRow(tables.Row):
    ajax = True

    def get_data(self, request, datacenter_id):
        datacenter = api.windc.datacenters_get(request, datacenter_id)
        datacenter.status = api.windc.datacenters_get_status(request,
                                                             datacenter_id)
        return datacenter


STATUS_DISPLAY_CHOICES = (
    ('deploying', 'Deploy in progress'),
    ('open', 'Ready to deploy')
)


def get_datacenter_status(datacenter):
    return datacenter.status


class WinDCTable(tables.DataTable):

    STATUS_CHOICES = (
        (None, True),
        ('Ready to deploy', False),
        ('deploying', True),
        ('deployed', True),
        ('ready', True),
        ('error', False),
    )

    name = tables.Column('name',
                         link=('horizon:project:windc:services'),
                         verbose_name=_('Name'))

    status = tables.Column(get_datacenter_status, verbose_name=_('Status'),
                           status=True,
                           status_choices=STATUS_CHOICES,
                           display_choices=STATUS_DISPLAY_CHOICES)

    class Meta:
        name = 'windc'
        verbose_name = _('Windows Data Centers')
        row_class = UpdateDCRow
        table_actions = (CreateDataCenter,)
        status_columns = ['status']
        row_actions = (ShowDataCenterServices, DeleteDataCenter,
                       DeployDataCenter)


class WinServicesTable(tables.DataTable):

    name = tables.Column('name', verbose_name=_('Name'),
                         link=('horizon:project:windc:service_details'),)
    _type = tables.Column('service_type', verbose_name=_('Type'))

    class Meta:
        name = 'services'
        verbose_name = _('Services')
        table_actions = (CreateService,)
        row_actions = (DeleteService,)
