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

import json
import logging
import re

from django.utils.text import normalize_newlines
from django.utils.translation import ugettext as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class SelectProjectUserAction(workflows.Action):
    project_id = forms.ChoiceField(label=_("Project"))
    user_id = forms.ChoiceField(label=_("User"))

    def __init__(self, request, *args, **kwargs):
        super(SelectProjectUserAction, self).__init__(request, *args, **kwargs)
        # Set our project choices
        projects = [(tenant.id, tenant.name)
                    for tenant in request.user.authorized_tenants]
        self.fields['project_id'].choices = projects

        # Set our user options
        users = [(request.user.id, request.user.username)]
        self.fields['user_id'].choices = users

    class Meta:
        name = _("Project & User")
        # Unusable permission so this is always hidden. However, we
        # keep this step in the workflow for validation/verification purposes.
        permissions = ("!",)


class SelectProjectUser(workflows.Step):
    action_class = SelectProjectUserAction


class ConfigureDCAction(workflows.Action):
    name = forms.CharField(label=_("Data Center Name"),
                              required=True)

    class Meta:
        name = _("Data Center")
        help_text_template = ("project/windc/_data_center_help.html")


class ConfigureDC(workflows.Step):
    action_class = ConfigureDCAction
    contibutes = ('name',)

    def contribute(self, data, context):
        if data:
            context['name'] = data.get('name', '')
        return context


class ConfigureWinDCAction(workflows.Action):
    dc_name = forms.CharField(label=_("Domain Name"),
                              required=False)

    #dc_net_name = forms.CharField(label=_("Domain NetBIOS Name"),
    #                              required=False,
    #                              help_text=_("A NetBIOS name of new domain."))

    dc_count = forms.IntegerField(label=_("Domain Controllers Count"),
                                  required=True,
                                  min_value=1,
                                  max_value=100,
                                  initial=1)

    adm_password = forms.CharField(widget=forms.PasswordInput,
                                   label=_("Administrator password"),
                                   required=False,
                                   help_text=_("Password for "
                                               "administrator account."))

    recovery_password = forms.CharField(widget=forms.PasswordInput,
                                   label=_("Recovery password"),
                                   required=False,
                                   help_text=_("Password for "
                                               "Active Directory "
                                               "Recovery Mode."))

    class Meta:
        name = _("Domain Controllers")
        help_text_template = ("project/windc/_dc_help.html")


class ConfigureWinDC(workflows.Step):
    action_class = ConfigureWinDCAction
    contibutes = ('dc_name', 'dc_count', 'adm_password', 'recovery_password')

    def contribute(self, data, context):
        if data:
            context['dc_name'] = data.get('dc_name', '')
            context['dc_count'] = data.get('dc_count', 1)
            context['adm_password'] = data.get('adm_password', '')
            context['recovery_password'] = data.get('recovery_password', '')
            context['type'] = 'active_directory_service'
        return context


class ConfigureWinIISAction(workflows.Action):
    iis_name = forms.CharField(label=_("IIS Server Name"),
                               required=False)

    iis_count = forms.IntegerField(label=_("IIS Servers Count"),
                                   required=True,
                                   min_value=1,
                                   max_value=100,
                                   initial=1)

    iis_domain = forms.CharField(label=_("Member of the Domain"),
                                 required=False,
                                 help_text=_("A name of domain for"
                                             " IIS Server."))

    class Meta:
        name = _("Internet Information Services")
        help_text_template = ("project/windc/_iis_help.html")


class ConfigureWinIIS(workflows.Step):
    action_class = ConfigureWinIISAction

    contibutes = ('iis_name', 'iis_count', 'iis_domain')

    def contribute(self, data, context):
        if data:
            context['iis_name'] = data.get('iis_name', '')
            context['iis_count'] = data.get('iis_count', 1)
            context['iis_domain'] = data.get('iis_domain', '')
        return context


class CreateWinService(workflows.Workflow):
    slug = "create"
    name = _("Create Service")
    finalize_button_name = _("Deploy")
    success_message = _('Created service "%s".')
    failure_message = _('Unable to create service "%s".')
    success_url = "/project/windc/%s/"
    default_steps = (SelectProjectUser,
                     ConfigureWinDC,
                     ConfigureWinIIS)
    
    def format_status_message(self, message):
        dc_name = self.context.get('dc_name', 'noname')
        return message % dc_name

    def handle(self, request, context):
        try:
            ############## FIX ME:
            link = request.__dict__['META']['HTTP_REFERER']
            datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]
            ##############

            self.success_url = "/project/windc/%s/" % datacenter_id

            service = api.windc.services_create(request,
                                                datacenter_id,
                                                context)
            return True
        except:
            exceptions.handle(request)
            return False



class CreateWinDC(workflows.Workflow):
    slug = "create"
    name = _("Create Windows Data Center")
    finalize_button_name = _("Create")
    success_message = _('Created data center "%s".')
    failure_message = _('Unable to create data center "%s".')
    success_url = "horizon:project:windc:index"
    default_steps = (SelectProjectUser,
                     ConfigureDC)

    def format_status_message(self, message):
        name = self.context.get('name', 'noname')
        return message % name

    def handle(self, request, context):
        try:
            datacenter = api.windc.datacenters_create(request, context)
            return True
        except:
            exceptions.handle(request)
            return False
