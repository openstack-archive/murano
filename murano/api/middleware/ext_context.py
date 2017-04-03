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

from keystoneauth1 import exceptions
from keystoneauth1.identity import v3
from keystoneauth1 import session as ks_session
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
        # services as murano recipients. The same is right for project and user
        # domain names.

        auth_url = CONF.cfapi.auth_url
        if not (auth_url.endswith('v2.0') or auth_url.endswith('v3')):
            auth_url += '/v3'
        elif auth_url.endswith('v2.0'):
            auth_url = auth_url.replace('v2.0', 'v3')
        elif auth_url.endswith('v3'):
            pass
        else:
            LOG.warning('Wrong format for service broker auth url')

        kwargs = {'auth_url': auth_url,
                  'username': user,
                  'password': password,
                  'project_name': CONF.cfapi.tenant,
                  'user_domain_name': CONF.cfapi.user_domain_name,
                  'project_domain_name': CONF.cfapi.project_domain_name}
        password_auth = v3.Password(**kwargs)
        session = ks_session.Session(auth=password_auth)

        self._query_endpoints(password_auth, session)

        return session.get_token()

    def _query_endpoints(self, auth, session):
        if not hasattr(self, '_murano_endpoint'):
            try:
                self._murano_endpoint = auth.get_endpoint(
                    session, 'application-catalog')
            except exceptions.EndpointNotFound:
                pass
        if not hasattr(self, '_glare_endpoint'):
            try:
                self._glare_endpoint = auth.get_endpoint(
                    session, 'artifact')
            except exceptions.EndpointNotFound:
                pass

    def get_endpoints(self):
        return {
            'murano': getattr(self, '_murano_endpoint', None),
            'glare': getattr(self, '_glare_endpoint', None),
        }

    def process_request(self, req):

        """Get keystone token for external request

        This middleware is used for external requests. It get credentials from
        request and try to get keystone token for further authorization.

        :param req: wsgi request object that will be given the context object
        """
        try:
            credentials = base64.b64decode(
                req.headers['Authorization'].split(' ')[1])
            user, password = credentials.decode('utf-8').split(':', 2)
            req.headers['X-Auth-Token'] = self.get_keystone_token(user,
                                                                  password)
            req.endpoints = self.get_endpoints()
        except KeyError:
            msg = _("Authorization required")
            LOG.warning(msg)
            raise exc.HTTPUnauthorized(explanation=msg)
        except exceptions.Unauthorized:
            msg = _("Your credentials are wrong. Please try again")
            LOG.warning(msg)
            raise exc.HTTPUnauthorized(explanation=msg)

    @classmethod
    def factory(cls, global_conf, **local_conf):
        def filter(app):
            return cls(app)
        return filter
