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

import functools as func

from oslo_log import log as logging
from webob import exc

from murano.api.v1 import request_statistics
from murano.common.helpers import token_sanitizer
from murano.common.i18n import _
from murano.common import wsgi
from murano.db.services import core_services
from murano import utils


LOG = logging.getLogger(__name__)

API_NAME = 'Services'


def normalize_path(f):
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
    @utils.verify_env
    @normalize_path
    def get(self, request, environment_id, path):
        LOG.debug('Services:Get <EnvId: {env_id}, '
                  'Path: {path}>'.format(env_id=environment_id, path=path))

        session_id = None
        if hasattr(request, 'context') and request.context.session:
            session_id = request.context.session

        try:
            result = core_services.CoreServices.get_data(environment_id,
                                                         path,
                                                         session_id)
        except (KeyError, ValueError, AttributeError):
            raise exc.HTTPNotFound
        return result

    @request_statistics.stats_count(API_NAME, 'Create')
    @utils.verify_session
    @utils.verify_env
    @normalize_path
    def post(self, request, environment_id, path, body=None):
        if not body:
            msg = _('Request body is empty: please, provide '
                    'application object model')
            LOG.error(msg)
            raise exc.HTTPBadRequest(msg)
        secure_data = token_sanitizer.TokenSanitizer().sanitize(body)
        LOG.debug('Services:Post <EnvId: {env_id}, Path: {path}, '
                  'Body: {body}>'.format(env_id=environment_id,
                                         body=secure_data, path=path))

        post_data = core_services.CoreServices.post_data
        session_id = request.context.session
        try:
            result = post_data(environment_id, session_id, body, path)
        except (KeyError, ValueError):
            raise exc.HTTPNotFound
        return result

    @request_statistics.stats_count(API_NAME, 'Update')
    @utils.verify_session
    @utils.verify_env
    @normalize_path
    def put(self, request, environment_id, path, body=None):
        if not body:
            body = []
        LOG.debug('Services:Put <EnvId: {0}, Path: {2}, '
                  'Body: {1}>'.format(environment_id, body, path))

        put_data = core_services.CoreServices.put_data
        session_id = request.context.session

        try:
            result = put_data(environment_id, session_id, body, path)
        except (KeyError, ValueError):
            raise exc.HTTPNotFound
        return result

    @request_statistics.stats_count(API_NAME, 'Delete')
    @utils.verify_session
    @utils.verify_env
    @normalize_path
    def delete(self, request, environment_id, path):
        LOG.debug('Services:Delete <EnvId: {0}, '
                  'Path: {1}>'.format(environment_id, path))

        delete_data = core_services.CoreServices.delete_data
        session_id = request.context.session

        try:
            delete_data(environment_id, session_id, path)
        except (KeyError, ValueError):
            raise exc.HTTPNotFound


def create_resource():
    return wsgi.Resource(Controller())
