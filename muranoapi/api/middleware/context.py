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

from oslo.config import cfg

import muranoapi.context
import muranoapi.openstack.common.wsgi as wsgi
import muranoapi.openstack.common.log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ContextMiddleware(wsgi.Middleware):
    def process_request(self, req):
        """Convert authentication information into a request context

        Generate a muranoapi.context.RequestContext object from the available
        authentication headers and store on the 'context' attribute
        of the req object.

        :param req: wsgi request object that will be given the context object
        """
        kwargs = {
            'user': req.headers.get('X-User-Id'),
            'tenant': req.headers.get('X-Tenant-Id'),
            'auth_token': req.headers.get('X-Auth-Token'),
            'session': req.headers.get('X-Configuration-Session')
        }
        req.context = muranoapi.context.RequestContext(**kwargs)

    @classmethod
    def factory(cls, global_conf, **local_conf):
        def filter(app):
            return cls(app)
        return filter
