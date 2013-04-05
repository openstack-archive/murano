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

from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import tabs
import logging

from tabula.tabula import api


LOG = logging.getLogger(__name__)


class OverviewTab(tabs.Tab):
    name = _("Service")
    slug = "_service"
    template_name = '_services.html'

    def get_context_data(self, request):
        data = self.tab_group.kwargs['service']

        return {"service_name": data.name,
                "service_status": data.status,
                "service_type": data.service_type,
                "service_domain": data.domain}


class LogsTab(tabs.Tab):
    name = _("Logs")
    slug = "_logs"
    template_name = '_service_logs.html'

    def get_context_data(self, request):
        data = self.tab_group.kwargs['service']

        reports = api.get_status_message_for_service(request, data.id)

        return {"reports": reports}


class ServicesTabs(tabs.TabGroup):
    slug = "services_details"
    tabs = (OverviewTab, LogsTab)
    sticky = True
