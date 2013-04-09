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
from webob import exc
from glazierapi.db.models import Session
from glazierapi.db.session import get_session

log = logging.getLogger(__name__)


def verify_session(func):
    @functools.wraps(func)
    def __inner(self, request, *args, **kwargs):
        if hasattr(request, 'context') and request.context.session:
            uw = get_session().query(Session)
            configuration_session = uw.get(request.context.session)

            if configuration_session.state != 'open':
                log.info('Session is already deployed')
                raise exc.HTTPUnauthorized
        else:
            log.info('No session is supplied')
            raise exc.HTTPUnauthorized
        return func(self, request, *args, **kwargs)
    return __inner
