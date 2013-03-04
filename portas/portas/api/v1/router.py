# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
# All Rights Reserved.
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
import routes
from portas.openstack.common import wsgi
from portas.api.v1 import environments
from portas.api.v1 import services


class API(wsgi.Router):
    @classmethod
    def factory(cls, global_conf, **local_conf):
        return cls(routes.Mapper())

    def __init__(self, mapper):
        environments_resource = environments.create_resource()
        mapper.connect('/environments',
                       controller=environments_resource,
                       action='index',
                       conditions={'method': ['GET']})
        mapper.connect('/environments',
                       controller=environments_resource,
                       action='create',
                       conditions={'method': ['POST']})
        mapper.connect('/environments/{environment_id}',
                       controller=environments_resource,
                       action='update',
                       conditions={'method': ['PUT']})
        mapper.connect('/environments/{environment_id}',
                       controller=environments_resource,
                       action='show',
                       conditions={'method': ['GET']})
        mapper.connect('/environments/{environment_id}',
                       controller=environments_resource,
                       action='delete',
                       conditions={'method': ['DELETE']})

        super(API, self).__init__(mapper)


class SessionEnabledAPI(wsgi.Router):
    @classmethod
    def factory(cls, global_conf, **local_conf):
        return cls(routes.Mapper())

    def __init__(self, mapper):
        services_resource = services.create_resource()
        mapper.connect('/environments/{environment_id}/activeDirectories',
                       controller=services_resource,
                       action='index',
                       conditions={'method': ['GET']})

        super(SessionEnabledAPI, self).__init__(mapper)