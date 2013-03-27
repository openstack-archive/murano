import functools
import logging
from webob import exc
from portas.db.models import Session
from portas.db.session import get_session

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
