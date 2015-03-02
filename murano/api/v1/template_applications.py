
#    Copyright (c) 2015 Telefonica I+D.
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

import functools as func

from webob import exc


from murano.api.v1 import request_statistics
from murano.common.helpers import token_sanitizer
from murano.common import wsgi
from murano.db.services import core_services
from murano.openstack.common import log as logging
from murano import utils


LOG = logging.getLogger(__name__)

API_NAME = 'Services'


def normalize_path(f):
    """It normalizes the path obtaining in the requests.
       It is used in all the operations in the controller
    """
    @func.wraps(f)
    def f_normalize_path(*args, **kwargs):
        if 'path' in kwargs:
            if kwargs['path']:
                kwargs['path'] = '/services/' + kwargs['path']
            else:
                kwargs['path'] = '/services'
        return f(*args, **kwargs)

    return f_normalize_path


class Controller(object):
    @request_statistics.stats_count(API_NAME, 'Index')
    @utils.verify_env_template
    @normalize_path
    def index(self, request, env_template_id, path):
        """It obtains all the services/applications associated to
           a template
           :param request: The operation request.
           :param env_template_id: The environment template id with
           contains the services
           :param path: The operation path
        """
        LOG.debug('Applications:Get <EnvTemplateId: {0}, '
                  'Path: {1}>'.format(env_template_id, path))

        try:
            get_data = core_services.CoreServices.get_template_data
            result = get_data(env_template_id, path)
        except (KeyError, ValueError, AttributeError):
            msg = 'The environment template does not exist' + env_template_id
            LOG.exception(msg)
            raise exc.HTTPNotFound(msg)
        return result

    @request_statistics.stats_count(API_NAME, 'Show')
    @utils.verify_env_template
    @normalize_path
    def show(self, request, env_template_id, path):
        """It shows the service description.
        :param request: The operation request.
        :param env_template_id: the env template ID where the service
        belongs to.
        :param path: The path include the service id
        :return: the service description.
        """
        LOG.debug('Applications:Get <EnvTemplateId: {0}, '
                  'Path: {1}>'.format(env_template_id, path))

        try:
            get_data = core_services.CoreServices.get_template_data
            result = get_data(env_template_id, path)
        except (KeyError, ValueError, AttributeError):
            msg = 'The template does not exist' + env_template_id
            LOG.exception(msg)
            raise exc.HTTPNotFound(msg)
        return result

    @request_statistics.stats_count(API_NAME, 'Create')
    @utils.verify_env_template
    @normalize_path
    def post(self, request, env_template_id, path, body):
        """It adds a service into a template.
        :param request: The operation request.
        :param env_template_id: the env template ID where the
        service belongs to.
        :param path: The path
        :param body: the information about the service
        :return: the service description.
        """
        secure_data = token_sanitizer.TokenSanitizer().sanitize(body)
        LOG.debug('Applications:Post <EnvTempId: {0}, Path: {2}, '
                  'Body: {1}>'.format(env_template_id, secure_data, path))

        post_data = core_services.CoreServices.post_application_data
        try:
            result = post_data(env_template_id, body, path)
        except (KeyError, ValueError):
            msg = 'The template does not exist ' + env_template_id
            LOG.exception(msg)
            raise exc.HTTPNotFound(msg)
        return result

    @request_statistics.stats_count(API_NAME, 'Update')
    @utils.verify_env_template
    @normalize_path
    def put(self, request, env_template_id, path, body):

        """It updates a service into a template.
        :param request: The operation request.
        :param env_template_id: the env template ID where the service
        belongs to.
        :param path: The path
        :param body: the information about the service
        :return: the service description updated.
        """
        LOG.debug('Applications:Put <EnvTempId: {0}, Path: {2}, '
                  'Body: {1}>'.format(env_template_id, body, path))

        put_data = core_services.CoreServices.put_data
        session_id = request.context.session

        try:
            result = put_data(env_template_id, session_id, body, path)
        except (KeyError, ValueError):
            msg = 'The template does not exist' + env_template_id
            LOG.exception(msg)
            raise exc.HTTPNotFound(msg)
        return result

    @request_statistics.stats_count(API_NAME, 'Delete')
    @utils.verify_env_template
    @normalize_path
    def delete(self, request, env_template_id, path):
        """It deletes a service into a template.
        :param request: The operation request.
        :param env_template_id: the env template ID where
        the service belongs to.
        :param path: The path contains the service id
        """
        LOG.debug('Applications:Put <EnvTempId: {0}, '
                  'Path: {1}>'.format(env_template_id, path))
        delete_data = core_services.CoreServices.delete_env_template_data
        try:
            delete_data(env_template_id, path)
        except (KeyError, ValueError):
            msg = 'The template does not exist' + env_template_id
            LOG.exception(msg)
            raise exc.HTTPNotFound(msg)


def create_resource():
    return wsgi.Resource(Controller())
