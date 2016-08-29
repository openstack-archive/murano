#    Copyright (c) 2014 Mirantis, Inc.
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

from oslo_serialization import jsonutils
from six.moves import http_client
import webob.dec

from murano.common import wsgi


class Controller(object):

    """A wsgi controller that reports which API versions are supported."""

    def index(self, req):
        """Respond to a request for all OpenStack API versions."""
        def build_version_object(version, path, status):
            return {
                'id': 'v%s' % version,
                'status': status,
                'links': [
                    {
                        'rel': 'self',
                        'href': '%s/%s/' % (req.host_url, path),
                    },
                ],
            }

        version_objs = []
        version_objs.extend([
            build_version_object(1.0, 'v1', 'CURRENT'),
        ])

        response = webob.Response(request=req,
                                  status=http_client.MULTIPLE_CHOICES,
                                  content_type='application/json')
        response.body = jsonutils.dumps(dict(versions=version_objs))
        return response

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        return self.index(req)


def create_resource(conf):
    return wsgi.Resource(Controller())
