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


class API(wsgi.Router):
    @classmethod
    def factory(cls, global_conf, **local_conf):
        return cls(routes.Mapper())

    def __init__(self, mapper):
        environments_resource = environments.create_resource()
        mapper.resource("environment", "environments", controller=environments_resource)
        super(API, self).__init__(mapper)
