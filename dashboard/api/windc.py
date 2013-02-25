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
import urlparse

from django.utils.decorators import available_attrs
from windcclient.v1 import client as windc_client


LOG = logging.getLogger(__name__)


def windcclient(request):
    o = urlparse.urlparse("http://127.0.0.1:8082")
    url = "http://127.0.0.1:8082/foo"
    LOG.debug('windcclient connection created using token "%s" and url "%s"'
              % (request.user.token, url))
    return windc_client.Client(endpoint=url, token=None)

def datacenters_create(request, parameters):
    name = parameters.get('name', '')
    return windcclient(request).datacenters.create(name)

def datacenters_delete(request, datacenter_id):
    return windcclient(request).datacenters.delete(datacenter_id)

def datacenters_get(request, datacenter_id):
    return windcclient(request).datacenters.get(datacenter_id)

def datacenters_list(request):
    return windcclient(request).datacenters.list()

def services_create(request, datacenter, parameters):
    name = parameters.get('dc_name', '')
    return windcclient(request).services.create(datacenter, name)

def services_list(request, datacenter):
    return windcclient(request).services.list(datacenter)

def services_get(request, datacenter, service_id):
    return windcclient(request).services.get(datacenter, service_id)

def services_delete(request, datacenter, service_id):
    return windcclient(request).services.delete(datacenter, service_id)
