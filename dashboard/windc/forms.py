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

import logging

from django import forms
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import api

from horizon import forms
from horizon import exceptions
from horizon import messages

import pdb

LOG = logging.getLogger(__name__)


class WizardFormServiceType(forms.Form):
    service = forms.ChoiceField(label=_("Service Type"),
                                choices=[
                                ('Active Directory', 'Active Directory'),
                                ('IIS', 'Internet Information Services')
                                ])


class WizardFormConfiguration(forms.Form):
    "The functions for this class will dynamically create in views.py"
    pass


class WizardFormADConfiguration(forms.Form):
    dc_name = forms.CharField(label=_("Domain Name"),
                        required=False)

    dc_count = forms.IntegerField(label=_("Instances Count"),
                                  required=True,
                                  min_value=1,
                                  max_value=100,
                                  initial=1)

    adm_password = forms.CharField(widget=forms.PasswordInput,
                                   label=_("Administrator password"),
                                   required=False)

    recovery_password = forms.CharField(widget=forms.PasswordInput,
                                   label=_("Recovery password"),
                                   required=False)


class WizardFormIISConfiguration(forms.Form):
    iis_name = forms.CharField(label=_("IIS Server Name"),
                               required=False)

    adm_password = forms.CharField(widget=forms.PasswordInput,
                                   label=_("Administrator password"),
                                   required=False)

    iis_domain = forms.CharField(label=_("Member of the Domain"),
                                 required=False)

    domain_user_name = forms.CharField(label=_("Domain User Name"),
                               required=False)

    domain_user_password = forms.CharField(widget=forms.PasswordInput,
                                   label=_("Domain User Password"),
                                   required=False)


class UpdateWinDC(forms.SelfHandlingForm):
    tenant_id = forms.CharField(widget=forms.HiddenInput)
    data_center = forms.CharField(widget=forms.HiddenInput)
    name = forms.CharField(required=True)

    def handle(self, request, data):
        try:
            server = api.nova.server_update(request, data['data_center'],
                                            data['name'])
            messages.success(request,
                             _('Data Center "%s" updated.') % data['name'])
            return server
        except:
            redirect = reverse("horizon:project:windc:index")
            exceptions.handle(request,
                              _('Unable to update data center.'),
                              redirect=redirect)
