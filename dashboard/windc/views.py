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
from .tables import WinDCTable
from .workflows import CreateWinDC


LOG = logging.getLogger(__name__)


class IndexView(tables.DataTableView):
    table_class = WinDCTable
    template_name = 'project/windc/index.html'

    def get_data(self):
        # Gather our instances
        try:
            instances = api.nova.server_list(self.request)
        except:
            instances = []
            exceptions.handle(self.request,
                              _('Unable to retrieve instances.'))
        # Gather our flavors and correlate our instances to them
        if instances:
            try:
                flavors = api.nova.flavor_list(self.request)
            except:
                flavors = []
                exceptions.handle(self.request, ignore=True)

            full_flavors = SortedDict([(str(flavor.id), flavor)
                                        for flavor in flavors])
            # Loop through instances to get flavor info.
            for instance in instances:
                try:
                    flavor_id = instance.flavor["id"]
                    if flavor_id in full_flavors:
                        instance.full_flavor = full_flavors[flavor_id]
                    else:
                        # If the flavor_id is not in full_flavors list,
                        # get it via nova api.
                        instance.full_flavor = api.nova.flavor_get(
                            self.request, flavor_id)
                except:
                    msg = _('Unable to retrieve instance size information.')
                    exceptions.handle(self.request, msg)
        return instances


class CreateWinDCView(workflows.WorkflowView):
    workflow_class = CreateWinDC
    template_name = "project/windc/create.html"

    def get_initial(self):
        initial = super(CreateWinDCView, self).get_initial()
        initial['project_id'] = self.request.user.tenant_id
        initial['user_id'] = self.request.user.id
        return initial
