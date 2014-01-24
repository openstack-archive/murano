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
import logging
from muranoapi.db.services.sessions import SessionServices, SessionState
from webob import exc
from muranoapi.db.models import Session, Environment
from muranoapi.db.session import get_session
from muranoapi.openstack.common.gettextutils import _  # noqa

log = logging.getLogger(__name__)


def verify_env(func):
    @functools.wraps(func)
    def __inner(self, request, environment_id, *args, **kwargs):
        unit = get_session()
        environment = unit.query(Environment).get(environment_id)
        if environment is None:
            log.info(_("Environment with id '{0}'"
                       " not found".format(environment_id)))
            raise exc.HTTPNotFound()

        if hasattr(request, 'context'):
            if environment.tenant_id != request.context.tenant:
                log.info(_('User is not authorized to access'
                           ' this tenant resources'))
                raise exc.HTTPUnauthorized()

        return func(self, request, environment_id, *args, **kwargs)
    return __inner


def verify_session(func):
    @functools.wraps(func)
    def __inner(self, request, *args, **kwargs):
        if hasattr(request, 'context') and not request.context.session:
            log.info(_('Session is required for this call'))
            raise exc.HTTPForbidden()

        session_id = request.context.session

        unit = get_session()
        session = unit.query(Session).get(session_id)

        if session is None:
            log.info(_('Session <SessionId {0}> '
                       'is not found'.format(session_id)))
            raise exc.HTTPForbidden()

        if not SessionServices.validate(session):
            log.info(_('Session <SessionId {0}> '
                       'is invalid'.format(session_id)))
            raise exc.HTTPForbidden()

        if session.state == SessionState.deploying:
            log.info(_('Session <SessionId {0}> is already in '
                       'deployment state'.format(session_id)))
            raise exc.HTTPForbidden()
        return func(self, request, *args, **kwargs)
    return __inner
