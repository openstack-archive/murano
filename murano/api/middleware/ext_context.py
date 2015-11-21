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

import base64

from keystoneclient import exceptions
from keystoneclient.v3 import client
from oslo_config import cfg
from oslo_log import log
from webob import exc

from murano.common.i18n import _
from murano.common import wsgi

CONF = cfg.CONF
LOG = log.getLogger(__name__)


class ExternalContextMiddleware(wsgi.Middleware):
    def get_keystone_token(self, user, password):
        # TODO(starodubcevna): picking up project_name and auth_url from
        # section related to Cloud Foundry service broker is probably a duct
        # tape and should be rewritten as soon as we get more non-OpenStack
        # services as murano recipients.
        keystone = client.Client(username=user,
                                 password=password,
                                 project_name=CONF.cfapi.tenant,
                                 auth_url=CONF.cfapi.auth_url.replace(
                                     'v2.0', 'v3'))
        return keystone.auth_token

    def process_request(self, req):

        """Get keystone token for external request

        This middleware is used for external requests. It get credentials from
        request and try to get keystone token for futher authorization.

        :param req: wsgi request object that will be given the context object
        """

        credentials = base64.b64decode(
            req.headers['Authorization'].split(' ')[1])
        user, password = credentials.split(':', 2)
        try:
            req.headers['X-Auth-Token'] = self.get_keystone_token(user,
                                                                  password)
        except exceptions.Unauthorized:
            msg = _("Your credentials are wrong. Please try again")
            LOG.warning(msg)
            raise exc.HTTPUnauthorized(explanation=msg)

    @classmethod
    def factory(cls, global_conf, **local_conf):
        def filter(app):
            return cls(app)
        return filter
