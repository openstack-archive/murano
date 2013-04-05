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

from glazierclient.common import http
from glazierclient.v1 import environments, sessions, services


class Client(http.HTTPClient):
    """Client for the Glazier v1 API.

    :param string endpoint: A user-supplied endpoint URL for the service.
    :param string token: Token for authentication.
    :param integer timeout: Allows customization of the timeout for client
                            http requests. (optional)
    """

    def __init__(self, *args, **kwargs):
        """ Initialize a new client for the Glazier v1 API. """
        super(Client, self).__init__(*args, **kwargs)
        self.environments = environments.EnvironmentManager(self)
        self.sessions = sessions.SessionManager(self)
        self.activeDirectories = services.ActiveDirectoryManager(self)
        self.webServers = services.WebServerManager(self)
