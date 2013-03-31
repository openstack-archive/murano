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
import string

from django import forms
from django.utils.translation import ugettext_lazy as _
import re
from tabula.windc import api

log = logging.getLogger(__name__)


class PasswordField(forms.CharField):
    # Setup the Field
    def __init__(self, label, *args, **kwargs):
        super(PasswordField, self).__init__(min_length=7, required=True,
                                            label=label,
                                            widget=forms.PasswordInput(
                                                render_value=False),
                                            *args, **kwargs)

    def clean(self, value):

        # Setup Our Lists of Characters and Numbers
        characters = list(string.letters)
        special_characters = '!@#$%^&*()_+|\/.,~?><:{}'
        numbers = [str(i) for i in range(10)]

        # Assume False until Proven Otherwise
        numCheck = False
        charCheck = False
        specCharCheck = False

        # Loop until we Match
        for char in value:
            if not charCheck:
                if char in characters:
                    charCheck = True
            if not specCharCheck:
                if char in special_characters:
                    specCharCheck = True
            if not numCheck:
                if char in numbers:
                    numCheck = True
            if numCheck and charCheck and specCharCheck:
                break

        if not numCheck or not charCheck or not specCharCheck:
            raise forms.ValidationError(u'Your password must include at least \
                                          one letter, at least one number and \
                                          at least one special character.')

        return super(PasswordField, self).clean(value)


class WizardFormServiceType(forms.Form):
    service = forms.ChoiceField(label=_('Service Type'),
                                choices=[
                                    ('Active Directory', 'Active Directory'),
                                    ('IIS', 'Internet Information Services')
                                ])


class WizardFormConfiguration(forms.Form):
    'The functions for this class will dynamically create in views.py'
    pass


class WizardFormADConfiguration(forms.Form):
    dc_name = forms.CharField(label=_('Domain Name'),
                              required=True)

    dc_count = forms.IntegerField(label=_('Instances Count'),
                                  required=True,
                                  min_value=1,
                                  max_value=100,
                                  initial=1)

    adm_password = PasswordField(_('Administrator password'))

    recovery_password = PasswordField(_('Recovery password'))

    def __init__(self, request, *args, **kwargs):
        super(WizardFormADConfiguration, self).__init__(*args, **kwargs)


class WizardFormIISConfiguration(forms.Form):
    iis_name = forms.CharField(label=_('IIS Server Name'),
                               required=True)

    adm_password = PasswordField(_('Administrator password'))

    iis_domain = forms.ChoiceField(label=_('Member of the Domain'),
                                   required=False)

    def __init__(self, request, *args, **kwargs):
        super(WizardFormIISConfiguration, self).__init__(*args, **kwargs)

        link = request.__dict__['META']['HTTP_REFERER']
        datacenter_id = re.search('windc/(\S+)', link).group(0)[6:-1]

        domains = api.get_active_directories(request, datacenter_id)

        self.fields['iis_domain'].choices = [("", "")] + \
                                            [(domain.name, domain.name)
                                             for domain in domains]
