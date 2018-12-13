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

import six

from oslo_log import log as logging
from oslo_messaging.rpc import client
from webob import exc

from murano.common.i18n import _
from murano.common import policy
from murano.common import wsgi
from murano.services import static_actions


LOG = logging.getLogger(__name__)


class Controller(object):

    def execute(self, request, body):
        policy.check("execute_action", request.context, {})

        class_name = body.get('className')
        method_name = body.get('methodName')
        if not class_name or not method_name:
            msg = _('Class name and method name must be specified for '
                    'static action')
            LOG.error(msg)
            raise exc.HTTPBadRequest(msg)

        args = body.get('parameters')
        pkg_name = body.get('packageName')
        class_version = body.get('classVersion', '=0')

        LOG.debug('StaticAction:Execute <MethodName: {0}, '
                  'ClassName: {1}>'.format(method_name, class_name))

        credentials = {
            'token': request.context.auth_token,
            'project_id': request.context.tenant,
            'user_id': request.context.user
        }

        try:
            return static_actions.StaticActionServices.execute(
                method_name, class_name, pkg_name, class_version, args,
                credentials)
        except client.RemoteError as e:
            LOG.error('Exception during call of the method {method_name}: '
                      '{exc}'.format(method_name=method_name, exc=str(e)))
            if e.exc_type in (
                    'NoClassFound', 'NoMethodFound', 'NoPackageFound',
                    'NoPackageForClassFound', 'MethodNotExposed',
                    'NoMatchingMethodException'):
                raise exc.HTTPNotFound(e.value)
            elif e.exc_type == 'ContractViolationException':
                raise exc.HTTPBadRequest(e.value)
            raise exc.HTTPServiceUnavailable(e.value)
        except ValueError as e:
            LOG.error('Exception during call of the method {method_name}: '
                      '{exc}'.format(method_name=method_name,
                                     exc=six.text_type(e)))
            raise exc.HTTPBadRequest(six.text_type(e))


def create_resource():
    return wsgi.Resource(Controller())
