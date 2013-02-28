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


class WizardForm1(forms.Form):
    _type = forms.ChoiceField(label=_("Service Type"))


class WizardForm2(forms.Form):
    subject = forms.CharField(max_length=100)
    sender = forms.CharField(max_length=1)


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
