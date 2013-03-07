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
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Views for managing instances.
"""
import logging
import re

from django import http
from django import shortcuts
from django.views import generic
from django.core.urlresolvers import reverse, reverse_lazy
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from django.contrib.formtools.wizard.views import SessionWizardView

from horizon import exceptions
from horizon import forms
from horizon import tabs
from horizon import tables
from horizon import workflows
from horizon.forms.views import ModalFormMixin

from openstack_dashboard import api
from .tables import WinDCTable, WinServicesTable
from .workflows import CreateWinDC
from .forms import (WizardFormServiceType, WizardFormConfiguration,
                    WizardFormADConfiguration, WizardFormIISConfiguration)

from horizon import messages

from django.http import HttpResponseRedirect
LOG = logging.getLogger(__name__)


class Wizard(ModalFormMixin, SessionWizardView, generic.FormView):
    template_name = 'project/windc/services_tabs.html'

    def done(self, form_list, **kwargs):
        link = self.request.__dict__['META']['HTTP_REFERER']
        datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]
        url = "/project/windc/%s/" % datacenter_id

        service_type = form_list[0].data.get('0-service', '')
        parameters = {}
        if form_list[1].data:
            data = form_list[1].data

        if service_type == 'active directory':
            parameters['dc_name'] = str(data.get('1-dc_name', 'noname'))
            parameters['adm_password'] = str(data.get('1-adm_password', ''))
            parameters['dc_count'] = int(data.get('1-dc_count', 1))
            parameters['recovery_password'] = \
                        str(data.get('1-recovery_password', ''))
        elif service_type == 'iis':
            parameters['iis_name'] = str(data.get('1-iis_name', 'noname'))
            parameters['adm_password'] = str(data.get('1-adm_password', ''))
            parameters['iis_count'] = int(data.get('1-iis_count', 1))
            parameters['iis_domain'] = str(data.get('1-iis_domain', ''))
            parameters['domain_user_name'] = \
                        str(data.get('1-domain_user_name', ''))
            parameters['domain_user_password'] = \
                        str(data.get('1-domain_user_password', ''))

        service = api.windc.services_create(self.request,
                                            datacenter_id,
                                            parameters)

        message = "The %s service successfully created." % service_type
        messages.success(self.request, message)
        return HttpResponseRedirect(url)

    def get_form(self, step=None, data=None, files=None):
        form = super(Wizard, self).get_form(step, data, files)
        LOG.debug("********" + str(self.form_list))
        if data:
            service_type = data.get('0-service', '')

            if service_type == 'active directory':
                self.form_list['1'] = WizardFormADConfiguration
            elif service_type == 'iis':
                self.form_list['1'] = WizardFormIISConfiguration

        return form


class IndexView(tables.DataTableView):
    table_class = WinDCTable
    template_name = 'project/windc/index.html'

    def get_data(self):
        # Gather our datacenters
        try:
            data_centers = api.windc.datacenters_list(self.request)
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
        data = self.get_data()
        context["dc_name"] = self.dc_name
        return context

    def get_data(self):
        try:
            dc_id = self.kwargs['data_center_id']
            datacenter = api.windc.datacenters_get(self.request, dc_id)
            self.dc_name = datacenter.name
            services = api.windc.services_list(self.request, datacenter)
        except:
            services = []
            exceptions.handle(self.request,
                              _('Unable to retrieve list of services for '
                              'data center "%s".') % dc_id)
        return services


class CreateWinDCView(workflows.WorkflowView):
    workflow_class = CreateWinDC
    template_name = "project/windc/create_dc.html"

    def get_initial(self):
        initial = super(CreateWinDCView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        return initial
