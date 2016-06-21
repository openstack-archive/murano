#    Copyright (c) 2016 Mirantis, Inc.
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

from oslo_log import log as logging
from oslo_messaging.rpc import client
import six
from webob import exc

from murano.api.v1 import request_statistics
from murano.common import policy
from murano.common import rpc
from murano.common import wsgi


LOG = logging.getLogger(__name__)
API_NAME = 'Schemas'


class Controller(object):
    @request_statistics.stats_count(API_NAME, 'GetSchema')
    def get_schema(self, request, class_name, method_names=None):
        LOG.debug('GetSchema:GetSchema')
        target = {"class_name": class_name}
        policy.check("get_schema", request.context, target)
        class_version = request.GET.get('classVersion')
        package_name = request.GET.get('packageName')
        credentials = {
            'token': request.context.auth_token,
            'project_id': request.context.tenant
        }

        try:
            methods = (list(
                six.moves.map(six.text_type.strip, method_names.split(',')))
                if method_names else [])
            return rpc.engine().generate_schema(
                credentials, class_name, methods,
                class_version, package_name)
        except client.RemoteError as e:
            if e.exc_type in ('NoClassFound',
                              'NoPackageForClassFound',
                              'NoPackageFound'):
                raise exc.HTTPNotFound(e.value)
            raise


def create_resource():
    return wsgi.Resource(Controller())
