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
from functools import wraps

from webob.exc import HTTPNotFound

from muranoapi import utils
from muranoapi.db.services.core_services import CoreServices
from muranoapi.openstack.common import wsgi
from muranoapi.openstack.common import log as logging
from muranocommon.helpers.token_sanitizer import TokenSanitizer

log = logging.getLogger(__name__)


def normalize_path(f):
    @wraps(f)
    def f_normalize_path(*args, **kwargs):
        if 'path' in kwargs:
            if kwargs['path']:
                kwargs['path'] = '/services/' + kwargs['path']
            else:
                kwargs['path'] = '/services'
        return f(*args, **kwargs)

    return f_normalize_path


class Controller(object):
    @utils.verify_env
    @normalize_path
    def get(self, request, environment_id, path):
        log.debug(_('Services:Get <EnvId: {0}, '
                    'Path: {1}>'.format(environment_id, path)))

        session_id = None
        if hasattr(request, 'context') and request.context.session:
            session_id = request.context.session

        try:
            result = CoreServices.get_data(environment_id, path, session_id)
        except (KeyError, ValueError):
            raise HTTPNotFound
        return result

    @utils.verify_session
    @utils.verify_env
    @normalize_path
    def post(self, request, environment_id, path, body):
        secure_data = TokenSanitizer().sanitize(body)
        log.debug(_('Services:Post <EnvId: {0}, Path: {2}, '
                    'Body: {1}>'.format(environment_id, secure_data, path)))

        post_data = CoreServices.post_data
        session_id = request.context.session
        try:
            result = post_data(environment_id, session_id, body, path)
        except (KeyError, ValueError):
            raise HTTPNotFound
        return result

    @utils.verify_session
    @utils.verify_env
    @normalize_path
    def put(self, request, environment_id, path, body):
        log.debug(_('Services:Put <EnvId: {0}, Path: {2}, '
                    'Body: {1}>'.format(environment_id, body, path)))

        put_data = CoreServices.put_data
        session_id = request.context.session

        try:
            result = put_data(environment_id, session_id, body, path)
        except (KeyError, ValueError):
            raise HTTPNotFound
        return result

    @utils.verify_session
    @utils.verify_env
    @normalize_path
    def delete(self, request, environment_id, path):
        log.debug(_('Services:Put <EnvId: {0}, '
                    'Path: {1}>'.format(environment_id, path)))

        delete_data = CoreServices.delete_data
        session_id = request.context.session

        try:
            delete_data(environment_id, session_id, path)
        except (KeyError, ValueError):
            raise HTTPNotFound


def create_resource():
    return wsgi.Resource(Controller())
