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

from tabula.windc import api


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
    name = forms.CharField(label=_("Data Center Name"), required=True)

    class Meta:
        name = _("Data Center")
        help_text_template = ("api_data_center_help.html")


class ConfigureDC(workflows.Step):
    action_class = ConfigureDCAction
    contibutes = ('name',)

    def contribute(self, data, context):
        if data:
            context['name'] = data.get('name', '')
        return context


class CreateWinDC(workflows.Workflow):
    slug = "create"
    name = _("Create Windows Data Center")
    finalize_button_name = _("Create")
    success_message = _('Created data center "%s".')
    failure_message = _('Unable to create data center "%s".')
    success_url = "horizon:project:windc:index"
    default_steps = (SelectProjectUser, ConfigureDC)

    def format_status_message(self, message):
        name = self.context.get('name', 'noname')
        return message % name

    def handle(self, request, context):
        try:
            datacenter = api.datacenters_create(request, context)
            return True
        except:
            exceptions.handle(request)
            return False
