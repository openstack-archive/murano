# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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
#    License for the specific language governing permissions and limitations#    under the License.

"""
Views for managing instances.
"""
import logging

from django import http
from django import shortcuts
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon import tables
from horizon import workflows

from openstack_dashboard import api
from .tables import WinDCTable, WinServicesTable
from .tabs import WinServicesTab
from .workflows import CreateWinService, CreateWinDC


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = WinDCTable
    template_name = 'project/windc/index.html'

    def get_data(self):
        # Gather our instances
        try:
            data_centers = api.windc.datacenter_list(self.request)
        except:
            data_centers = []
            exceptions.handle(self.request,
                              _('Unable to retrieve data centers list.'))
        return data_centers


class WinServices(tables.DataTableView):
    table_class = WinServicesTable
    template_name = 'project/windc/services.html'

    def get_context_data(self, **kwargs):
        context = super(WinServices, self).get_context_data(**kwargs)
        context["domain_controller_name"] = self.get_data()[0].name
        return context

    def get_data(self):
        try:
            dc_id = self.kwargs['domain_controller_id']
            domain_controller = api.windc.datacenter_get(self.request, dc_id)
        except:
            redirect = reverse('horizon:project:windc:index')
            exceptions.handle(self.request,
                              _('Unable to retrieve details for '
                              'domain_controller "%s".') % dc_id,
                              redirect=redirect)
        self._domain_controller = [domain_controller,]
        return self._domain_controller


class CreateWinDCView(workflows.WorkflowView):
    workflow_class = CreateWinDC
    template_name = "project/windc/create_dc.html"

    def get_initial(self):
        initial = super(CreateWinDCView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        return initial

class CreateWinServiceView(workflows.WorkflowView):
    workflow_class = CreateWinService
    template_name = "project/windc/create.html"

    def get_initial(self):
        initial = super(CreateWinServiceView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        return initial
