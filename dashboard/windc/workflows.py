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

from django.utils.text import normalize_newlines
from django.utils.translation import ugettext as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api
from openstack_dashboard.api import cinder
from openstack_dashboard.api import glance
from openstack_dashboard.usage import quotas


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


class ConfigureWinDCAction(workflows.Action):
    dc_name = forms.CharField(label=_("Domain Name"),
                              required=False,
                              help_text=_("A name of new domain."))

    dc_net_name = forms.CharField(label=_("Domain NetBIOS Name"),
                                  required=False,
                                  help_text=_("A NetBIOS name of new domain."))

    dc_count = forms.IntegerField(label=_("Domain Controllers Count"),
                                  required=True,
                                  min_value=1,
                                  max_value=100,
                                  initial=1,
                                  help_text=_("Domain Controllers count."))

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


class ConfigureWinIISAction(workflows.Action):
    iis_name = forms.CharField(label=_("IIS Server Name"),
                               required=False,
                               help_text=_("A name of IIS Server."))

    iis_count = forms.IntegerField(label=_("IIS Servers Count"),
                                   required=True,
                                   min_value=1,
                                   max_value=100,
                                   initial=1,
                                   help_text=_("IIS Servers count."))

    iis_domain = forms.CharField(label=_("Member of the Domain"),
                                 required=False,
                                 help_text=_("A name of domain for"
                                             " IIS Server."))

    class Meta:
        name = _("Internet Information Services")
        help_text_template = ("project/windc/_iis_help.html")


class ConfigureWinIIS(workflows.Step):
    action_class = ConfigureWinIISAction


class CreateWinService(workflows.Workflow):
    slug = "create"
    name = _("Create Windows Service")
    finalize_button_name = _("Deploy")
    success_message = _('Deployed %(count)s named "%(name)s".')
    failure_message = _('Unable to deploy %(count)s named "%(name)s".')
    success_url = "horizon:project:windc:index"
    default_steps = (SelectProjectUser,
                     ConfigureWinDC,
                     ConfigureWinIIS)

    ## TO DO:
    ## Need to rewrite the following code:

    #def handle(self, request, context):
    #    try:
    #        api.windc.create(request,...)
    #        return True
    #    except:
    #        exceptions.handle(request)
    #        return False
