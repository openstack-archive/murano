#    Copyright (c) 2015 Mirantis, Inc.
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

from murano.cfapi import cfapi
from murano.common import wsgi


class API(wsgi.Router):
    @classmethod
    def factory(cls, global_conf, **local_conf):
        return cls(routes.Mapper())

    def __init__(self, mapper):
        services_resource = cfapi.create_resource()
        mapper.connect('/v2/catalog',
                       controller=services_resource,
                       action='list',
                       conditions={'method': ['GET']})
        mapper.connect(('/v2/service_instances/{instance_id}'),
                       controller=services_resource,
                       action='provision',
                       conditions={'method': ['PUT']})
        mapper.connect(('/v2/service_instances/{instance_id}'),
                       controller=services_resource,
                       action='deprovision',
                       conditions={'method': ['DELETE']})

        mapper.connect(('/v2/service_instances/{instance_id}/service_bindings/'
                        '{app_id}'),
                       controller=services_resource,
                       action='bind',
                       conditions={'method': ['PUT']})

        mapper.connect(('/v2/service_instances/{instance_id}/service_bindings/'
                        '{app_id}'),
                       controller=services_resource,
                       action='unbind',
                       conditions={'method': ['DELETE']})

        mapper.connect(('/v2/service_instances/{instance_id}/last_operation'),
                       controller=services_resource,
                       action='get_last_operation',
                       conditions={'method': ['GET']})

        super(API, self).__init__(mapper)
