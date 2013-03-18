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
from portasclient.v1.client import Client as windc_client

LOG = logging.getLogger(__name__)


def windcclient(request):
    url = "http://127.0.0.1:8082"
    LOG.debug('windcclient connection created using token "%s" and url "%s"'
              % (request.user.token, url))
    return windc_client(endpoint=url, token=request.user.token.token['id'])


def datacenters_create(request, parameters):
    name = parameters.get('name', '')
    return windcclient(request).environments.create(name)


def datacenters_delete(request, datacenter_id):
    return windcclient(request).environments.delete(datacenter_id)


def datacenters_get(request, datacenter_id):
    return windcclient(request).environments.get(datacenter_id)


def datacenters_list(request):
    return windcclient(request).environments.list()


def datacenters_deploy(request, datacenter_id):
    sessions = windcclient(request).sessions.list(datacenter_id)
    for session in sessions:
        if session.state == 'open':
            session_id = session.id
    if not session_id:
        return "Sorry, nothing to deploy."
    return windcclient(request).sessions.deploy(datacenter_id, session_id)


def services_create(request, datacenter, parameters):
    session_id = windcclient(request).sessions.list(datacenter)[0].id
    if parameters['service_type'] == 'Active Directory':
        res = windcclient(request).activeDirectories.create(datacenter,
                                                            session_id,
                                                            parameters)
    else:
        res = windcclient(request).webServers.create(datacenter,
                                                     session_id,
                                                     parameters)

    return res


def services_list(request, datacenter_id):
    session_id = None
    sessions = windcclient(request).sessions.list(datacenter_id)
    LOG.critical('DC ID: ' + str(datacenter_id))
    
    for s in sessions:
        if s.state in ['open', 'deploying']:
            session_id = s.id

    if session_id is None:
        session_id = windcclient(request).sessions.configure(datacenter_id).id

    services = windcclient(request).activeDirectories.list(datacenter_id,
                                                           session_id)
    services += windcclient(request).webServers.list(datacenter_id, session_id)

    return services


def services_get(request, datacenter_id, service_id):
    services = services_list(request, datacenter_id)
    
    for service in services:
        if service.id is service_id:
            return service


def services_delete(request, datacenter_id, service_id):
    services = services_list(request, datacenter_id)

    session_id = None
    sessions = windcclient(request).sessions.list(datacenter_id)
    for session in sessions:
        if session.state == 'open':
            session_id = session.id

    if session_id is None:
        raise Exception("Sorry, you can not delete this service now.")

    for service in services:
        if service.id is service_id:
            if service.type is 'Active Directory':
                windcclient(request).activeDirectories.delete(datacenter_id,
                                                              session_id,
                                                              service_id)
            elif service.type is 'IIS':
                windcclient(request).webServers.delete(datacenter_id,
                                                       session_id,
                                                       service_id)
