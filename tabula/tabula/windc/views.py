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

from tabula.windc import api

from .tables import WinDCTable, WinServicesTable
from .workflows import CreateWinDC
from .tabs import WinServicesTabs
from .forms import (WizardFormServiceType, WizardFormConfiguration,
                    WizardFormADConfiguration, WizardFormIISConfiguration)

from horizon import messages

from django.http import HttpResponseRedirect
LOG = logging.getLogger(__name__)


class Wizard(ModalFormMixin, SessionWizardView, generic.FormView):
    template_name = 'services_tabs.html'

    def done(self, form_list, **kwargs):
        link = self.request.__dict__['META']['HTTP_REFERER']
        datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]
        
        LOG.critical("/////////////////////////////")
        LOG.critical(link)
        LOG.critical(datacenter_id)
        LOG.critical("/////////////////////////////")
        
        url = "/project/windc/%s/" % datacenter_id

        service_type = form_list[0].data.get('0-service', '')
        parameters = {'service_type': service_type}
        data = form_list[1].data
        if service_type == 'Active Directory':
            parameters['configuration'] = 'standalone'
            parameters['name'] = str(data.get('1-dc_name', 'noname'))
            parameters['domain'] = parameters['name'] # Fix Me in orchestrator
            parameters['adminPassword'] = str(data.get('1-adm_password', ''))
            dc_count = int(data.get('1-dc_count', 1))
            recovery_password = str(data.get('1-recovery_password', ''))
            parameters['units'] = []
            parameters['units'].append({'isMaster': True,
                                        'recoveryPassword': recovery_password,
                                        'location': 'west-dc'})
            for dc in range(dc_count - 1):
                parameters['units'].append({'isMaster': False,
                                        'recoveryPassword': recovery_password,
                                        'location': 'west-dc'})

        elif service_type == 'IIS':
            password = data.get('1-adm_password', '')
            parameters['name'] = str(data.get('1-iis_name', 'noname'))
            parameters['credentials'] = {'username': 'Administrator',
                                         'password': password}
            parameters['domain'] = str(data.get('1-iis_domain', ''))
            password = form_list[1].data.get('1-adm_password', '')
            domain = form_list[1].data.get('1-iis_domain', '')
            dc_user = form_list[1].data.get('1-domain_user_name', '')
            dc_pass = form_list[1].data.get('1-domain_user_password', '')
            parameters['name'] = str(form_list[1].data.get('1-iis_name',
                                                           'noname'))
            parameters['domain'] = parameters['name']
            parameters['credentials'] = {'username': 'Administrator',
                                         'password': password}
            parameters['domain'] = str(domain)
                                   # 'username': str(dc_user),
                                   # 'password': str(dc_pass)}
            parameters['location'] = 'west-dc'

            parameters['units'] = []
            parameters['units'].append({'id': '1',
                                        'endpoint': [{'host': '10.0.0.1'}],
                                        'location': 'west-dc'})

        service = api.services_create(self.request, datacenter_id, parameters)

        message = "The %s service successfully created." % service_type
        messages.success(self.request, message)
        return HttpResponseRedirect(url)

    def get_form(self, step=None, data=None, files=None):

        form = super(Wizard, self).get_form(step, data, files)
        if data:
            self.service_type = data.get('0-service', '')
            if self.service_type == 'Active Directory':
                self.form_list['1'] = WizardFormADConfiguration
            elif self.service_type == 'IIS':
                self.form_list['1'] = WizardFormIISConfiguration

        return form

    def get_form_kwargs(self, step=None):
        return {'request': self.request} if step == u'1' else {}

    def get_form_step_data(self, form):
        LOG.debug(form.data)
        return form.data

    def get_context_data(self, form, **kwargs):
        context = super(Wizard, self).get_context_data(form=form, **kwargs)
        if self.steps.index > 0:
            context.update({'service_type': self.service_type})
        return context


class IndexView(tables.DataTableView):
    table_class = WinDCTable
    template_name = 'index.html'

    def get_data(self):
        try:
            data_centers = api.datacenters_list(self.request)
        except:
            data_centers = []
            exceptions.handle(self.request,
                              _('Unable to retrieve data centers list.'))
        return data_centers


class WinServices(tables.DataTableView):
    table_class = WinServicesTable
    template_name = 'services.html'

    def get_context_data(self, **kwargs):
        context = super(WinServices, self).get_context_data(**kwargs)
        context['dc_name'] = self.dc_name
        return context

    def get_data(self):
        try:
            dc_id = self.kwargs['data_center_id']
            self.datacenter_id = dc_id
            datacenter = api.datacenters_get(self.request, dc_id)
            self.dc_name = datacenter.name
            services = api.services_list(self.request, dc_id)
        except:
            services = []
            exceptions.handle(self.request,
                              _('Unable to retrieve list of services for '
                                'data center "%s".') % self.dc_name)
        self._services = services
        return self._services


class DetailServiceView(tabs.TabView):
    tab_group_class = WinServicesTabs
    template_name = 'service_details.html'
    
    def get_context_data(self, **kwargs):
        context = super(DetailServiceView, self).get_context_data(**kwargs)
        context["service"] = self.get_data()
        context["service_name"] = self.get_data().name
        return context

    def get_data(self):
        if not hasattr(self, "_service"):
            try:
                service_id = self.kwargs['service_id']
                service = api.get_service_datails(self.request, service_id)
            except:
                redirect = reverse('horizon:project:windc:index')
                exceptions.handle(self.request,
                                  _('Unable to retrieve details for '
                                    'service "%s".') % service_id,
                                    redirect=redirect)
            self._service = service
        return self._service

    def get_tabs(self, request, *args, **kwargs):
        service = self.get_data()
        return self.tab_group_class(request, service=service, **kwargs)


class CreateWinDCView(workflows.WorkflowView):
    workflow_class = CreateWinDC
    template_name = 'create_dc.html'

    def get_initial(self):
        initial = super(CreateWinDCView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        return initial
