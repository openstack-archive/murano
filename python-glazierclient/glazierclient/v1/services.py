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

from glazierclient.common import base


class ActiveDirectory(base.Resource):
    def __repr__(self):
        return '<ActiveDirectory %s>' % self._info

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class ActiveDirectoryManager(base.Manager):
    resource_class = ActiveDirectory

    def list(self, environment_id, session_id=None):
        if session_id:
            headers = {'X-Configuration-Session': session_id}
        else:
            headers = {}

        return self._list('environments/{id}/activeDirectories'.
                          format(id=environment_id),
                          'activeDirectories',
                          headers=headers)

    def create(self, environment_id, session_id, active_directory):
        headers = {'X-Configuration-Session': session_id}

        return self._create('environments/{id}/activeDirectories'.
                            format(id=environment_id),
                            active_directory,
                            headers=headers)

    def delete(self, environment_id, session_id, service_id):
        headers = {'X-Configuration-Session': session_id}
        path = 'environments/{id}/activeDirectories/{active_directory_id}'
        path = path.format(id=environment_id, active_directory_id=service_id)

        return self._delete(path, headers=headers)


class WebServer(base.Resource):
    def __repr__(self):
        return '<WebServer %s>' % self._info

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class WebServerManager(base.Manager):
    resource_class = WebServer

    def list(self, environment_id, session_id=None):
        if session_id:
            headers = {'X-Configuration-Session': session_id}
        else:
            headers = {}

        return self._list('environments/{id}/webServers'.
                          format(id=environment_id),
                          'webServers',
                          headers=headers)

    def create(self, environment_id, session_id, web_server):
        headers = {'X-Configuration-Session': session_id}

        return self._create('environments/{id}/webServers'.
                            format(id=environment_id),
                            web_server,
                            headers=headers)

    def delete(self, environment_id, session_id, service_id):
        headers = {'X-Configuration-Session': session_id}

        return self._delete('environments/{id}/webServers/{web_server_id}'
                            .format(id=environment_id,
                                    web_server_id=service_id),
                            headers=headers)
