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

import functools

from webob import exc

from murano.common.i18n import _LI
from murano.db import models
from murano.db.services import sessions
from murano.db import session as db_session
from murano.openstack.common import log as logging
from murano.services import states

LOG = logging.getLogger(__name__)


def verify_env(func):
    @functools.wraps(func)
    def __inner(self, request, environment_id, *args, **kwargs):
        unit = db_session.get_session()
        environment = unit.query(models.Environment).get(environment_id)
        if environment is None:
            LOG.info(_LI("Environment with id '{0}'"
                         " not found").format(environment_id))
            raise exc.HTTPNotFound()

        if hasattr(request, 'context'):
            if environment.tenant_id != request.context.tenant:
                LOG.info(_LI('User is not authorized to access'
                             ' these tenant resources'))
                raise exc.HTTPUnauthorized()

        return func(self, request, environment_id, *args, **kwargs)
    return __inner


def verify_env_template(func):
    @functools.wraps(func)
    def __inner(self, request, env_template_id, *args, **kwargs):
        unit = db_session.get_session()
        template = unit.query(models.EnvironmentTemplate).get(env_template_id)
        if template is None:
            LOG.info(_LI("Environment Template with id '{0}' not found").
                     format(env_template_id))
            raise exc.HTTPNotFound()

        if hasattr(request, 'context'):
            if template.tenant_id != request.context.tenant:
                LOG.info(_LI('User is not authorized to access '
                             'this tenant resources'))
                raise exc.HTTPUnauthorized()

        return func(self, request, env_template_id, *args, **kwargs)
    return __inner


def verify_session(func):
    @functools.wraps(func)
    def __inner(self, request, *args, **kwargs):
        if hasattr(request, 'context') and not request.context.session:
            LOG.info(_LI('Session is required for this call'))
            raise exc.HTTPForbidden()

        session_id = request.context.session

        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        if session is None:
            LOG.info(_LI('Session <SessionId {0}> '
                         'is not found').format(session_id))
            raise exc.HTTPForbidden()

        if not sessions.SessionServices.validate(session):
            LOG.info(_LI('Session <SessionId {0}> '
                         'is invalid').format(session_id))
            raise exc.HTTPForbidden()

        if session.state == states.SessionState.DEPLOYING:
            LOG.info(_LI('Session <SessionId {0}> is already in '
                         'deployment state').format(session_id))
            raise exc.HTTPForbidden()
        return func(self, request, *args, **kwargs)
    return __inner
