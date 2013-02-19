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

#from horizon.api import base


__all__ = ('datacenter_get','datacenter_list',
           'datacenter_create','datacenter_delete')


LOG = logging.getLogger(__name__)


def windcclient(request):
    o = urlparse.urlparse("http://127.0.0.1:8082")
    url = "http://127.0.0.1:8082/foo"
    LOG.debug('windcclient connection created using token "%s" and url "%s"'
              % (request.user.token, url))
    return windc_client.Client(endpoint=url, token=None)

def datacenter_create(request, parameters):
    name = parameters.get('name')
    _type = parameters.get('type')
    version = parameters.get('version')
    ip = parameters.get('ip')
    port = parameters.get('port')
    user = parameters.get('user')
    password = parameters.get('password')
    return windcclient(request).datacenters.create(name, _type,
                                                   version, ip,
                                                   port, user, password)

def datacenter_delete(request, datacenter_id):
    return windcclient(request).datacenters.delete(datacenter_id)

def datacenter_get(request, datacenter_id):
    return windcclient(request).datacenters.get(datacenter_id)

def datacenter_list(request):
    return windcclient(request).datacenters.list()
