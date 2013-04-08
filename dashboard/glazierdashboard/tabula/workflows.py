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

import json
import logging
import re

from django.utils.text import normalize_newlines
from django.utils.translation import ugettext as _

from horizon import exceptions
from horizon import forms
from horizon import workflows

from glazierdashboard.tabula import api


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


class ConfigureEnvironmentAction(workflows.Action):
    name = forms.CharField(label=_("Environment Name"), required=True)

    class Meta:
        name = _("Environment")
        help_text_template = "_data_center_help.html"


class ConfigureEnvironment(workflows.Step):
    action_class = ConfigureEnvironmentAction
    contibutes = ('name',)

    def contribute(self, data, context):
        if data:
            context['name'] = data.get('name', '')
        return context


class CreateEnvironment(workflows.Workflow):
    slug = "create"
    name = _("Create Environment")
    finalize_button_name = _("Create")
    success_message = _('Created environment "%s".')
    failure_message = _('Unable to create environment "%s".')
    success_url = "horizon:project:tabula:index"
    default_steps = (SelectProjectUser, ConfigureEnvironment)

    def format_status_message(self, message):
        name = self.context.get('name', 'noname')
        return message % name

    def handle(self, request, context):
        try:
            api.environment_create(request, context)
            return True
        except:
            exceptions.handle(request)
            return False
