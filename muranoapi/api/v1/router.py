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
from muranoapi.openstack.common import wsgi
from muranoapi.api.v1 import environments, services
from muranoapi.api.v1 import sessions
from muranoapi.api.v1 import active_directories
from muranoapi.api.v1 import webservers
from muranoapi.api.v1 import aspNetApps
from muranoapi.api.v1 import webserverFarms
from muranoapi.api.v1 import aspNetAppFarms


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
                       '{session_id}/reports',
                       controller=sessions_resource,
                       action='reports',
                       conditions={'method': ['GET']})
        mapper.connect('/environments/{environment_id}/sessions/'
                       '{session_id}/deploy',
                       controller=sessions_resource,
                       action='deploy',
                       conditions={'method': ['POST']})

        activeDirectories_resource = active_directories.create_resource()
        mapper.connect('/environments/{environment_id}/activeDirectories',
                       controller=activeDirectories_resource,
                       action='index',
                       conditions={'method': ['GET']})
        mapper.connect('/environments/{environment_id}/activeDirectories',
                       controller=activeDirectories_resource,
                       action='create',
                       conditions={'method': ['POST']})
        mapper.connect('/environments/{environment_id}/activeDirectories/'
                       '{active_directory_id}',
                       controller=activeDirectories_resource,
                       action='delete',
                       conditions={'method': ['DELETE']})

        webServers_resource = webservers.create_resource()
        mapper.connect('/environments/{environment_id}/webServers',
                       controller=webServers_resource,
                       action='index',
                       conditions={'method': ['GET']})
        mapper.connect('/environments/{environment_id}/webServers',
                       controller=webServers_resource,
                       action='create',
                       conditions={'method': ['POST']})
        mapper.connect('/environments/{environment_id}/webServers/'
                       '{web_server_id}',
                       controller=webServers_resource,
                       action='delete',
                       conditions={'method': ['DELETE']})

        aspNetApps_resource = aspNetApps.create_resource()
        mapper.connect('/environments/{environment_id}/aspNetApps',
                       controller=aspNetApps_resource,
                       action='index',
                       conditions={'method': ['GET']})
        mapper.connect('/environments/{environment_id}/aspNetApps',
                       controller=aspNetApps_resource,
                       action='create',
                       conditions={'method': ['POST']})
        mapper.connect('/environments/{environment_id}/aspNetApps/'
                       '{app_id}',
                       controller=aspNetApps_resource,
                       action='delete',
                       conditions={'method': ['DELETE']})

        webServerFarms_resource = webserverFarms.create_resource()
        mapper.connect('/environments/{environment_id}/webServerFarms',
                       controller=webServerFarms_resource,
                       action='index',
                       conditions={'method': ['GET']})
        mapper.connect('/environments/{environment_id}/webServerFarms',
                       controller=webServerFarms_resource,
                       action='create',
                       conditions={'method': ['POST']})
        mapper.connect('/environments/{environment_id}/webServerFarms/'
                       '{web_server_farm_id}',
                       controller=webServerFarms_resource,
                       action='delete',
                       conditions={'method': ['DELETE']})

        aspNetAppFarms_resource = aspNetAppFarms.create_resource()
        mapper.connect('/environments/{environment_id}/aspNetAppFarms',
                       controller=aspNetAppFarms_resource,
                       action='index',
                       conditions={'method': ['GET']})
        mapper.connect('/environments/{environment_id}/aspNetAppFarms',
                       controller=aspNetAppFarms_resource,
                       action='create',
                       conditions={'method': ['POST']})
        mapper.connect('/environments/{environment_id}/aspNetAppFarms/'
                       '{app_farm_id}',
                       controller=aspNetAppFarms_resource,
                       action='delete',
                       conditions={'method': ['DELETE']})

        super(API, self).__init__(mapper)
