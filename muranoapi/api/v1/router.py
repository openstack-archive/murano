#    Copyright (c) 2013 Mirantis, Inc.
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

from muranoapi.api.v1 import catalog
from muranoapi.api.v1 import deployments
from muranoapi.api.v1 import environment_statistics
from muranoapi.api.v1 import environments
from muranoapi.api.v1 import services
from muranoapi.api.v1 import sessions
from muranoapi.openstack.common import wsgi


class API(wsgi.Router):
    @classmethod
    def factory(cls, global_conf, **local_conf):
        return cls(routes.Mapper())

    def __init__(self, mapper):
        services_resource = services.create_resource()
        mapper.connect('/environments/{environment_id}/services',
                       controller=services_resource,
                       action='get',
                       conditions={'method': ['GET']}, path='')
        mapper.connect('/environments/{environment_id}/services/{path:.*?}',
                       controller=services_resource,
                       action='get',
                       conditions={'method': ['GET']}, path='')

        mapper.connect('/environments/{environment_id}/services',
                       controller=services_resource,
                       action='post',
                       conditions={'method': ['POST']}, path='')
        mapper.connect('/environments/{environment_id}/services/{path:.*?}',
                       controller=services_resource,
                       action='post',
                       conditions={'method': ['POST']}, path='')

        mapper.connect('/environments/{environment_id}/services',
                       controller=services_resource,
                       action='put',
                       conditions={'method': ['PUT']}, path='')
        mapper.connect('/environments/{environment_id}/services/{path:.*?}',
                       controller=services_resource,
                       action='put',
                       conditions={'method': ['PUT']}, path='')

        mapper.connect('/environments/{environment_id}/services',
                       controller=services_resource,
                       action='delete',
                       conditions={'method': ['DELETE']}, path='')
        mapper.connect('/environments/{environment_id}/services/{path:.*?}',
                       controller=services_resource,
                       action='delete',
                       conditions={'method': ['DELETE']}, path='')

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
        mapper.connect('/environments/{environment_id}/lastStatus',
                       controller=environments_resource,
                       action='last',
                       conditions={'method': ['GET']})

        deployments_resource = deployments.create_resource()
        mapper.connect('/environments/{environment_id}/deployments',
                       controller=deployments_resource,
                       action='index',
                       conditions={'method': ['GET']})
        mapper.connect('/environments/{environment_id}/deployments/'
                       '{deployment_id}',
                       controller=deployments_resource,
                       action='statuses',
                       conditions={'method': ['GET']})

        sessions_resource = sessions.create_resource()
        mapper.connect('/environments/{environment_id}/configure',
                       controller=sessions_resource,
                       action='configure',
                       conditions={'method': ['POST']})
        mapper.connect('/environments/{environment_id}/sessions/{session_id}',
                       controller=sessions_resource,
                       action='show',
                       conditions={'method': ['GET']})
        mapper.connect('/environments/{environment_id}/sessions/{session_id}',
                       controller=sessions_resource,
                       action='delete',
                       conditions={'method': ['DELETE']})
        mapper.connect('/environments/{environment_id}/sessions/'
                       '{session_id}/deploy',
                       controller=sessions_resource,
                       action='deploy',
                       conditions={'method': ['POST']})

        statistics_resource = environment_statistics.create_resource()
        mapper.connect(
            '/environments/{environment_id}/statistics/{instance_id}',
            controller=statistics_resource,
            action='get_for_instance',
            conditions={'method': ['GET']})
        mapper.connect(
            '/environments/{environment_id}/statistics',
            controller=statistics_resource,
            action='get_for_environment',
            conditions={'method': ['GET']})

        catalog_resource = catalog.create_resource()
        mapper.connect('/catalog/packages/{package_id}',
                       controller=catalog_resource,
                       action='get',
                       conditions={'method': ['GET']})
        mapper.connect('/catalog/packages/{package_id}',
                       controller=catalog_resource,
                       action='update',
                       conditions={'method': ['PATCH']})
        mapper.connect('/catalog/packages',
                       controller=catalog_resource,
                       action='search',
                       conditions={'method': ['GET']})
        mapper.connect('/catalog/packages',
                       controller=catalog_resource,
                       action='upload',
                       conditions={'method': ['POST']})
        super(API, self).__init__(mapper)
