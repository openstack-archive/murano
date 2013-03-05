import functools
import logging
from webob import exc
from portas.db.api import SessionRepository

LOG = logging.getLogger(__name__)


def verify_session(func):
    @functools.wraps(func)
    def __inner(self, request, *args, **kwargs):
        if hasattr(request, 'context') and request.context.session:
            repo = SessionRepository()
            session = repo.get(request.context.session)
            if session.status != 'open':
                LOG.info('Session is already deployed')
                raise exc.HTTPUnauthorized
        else:
            LOG.info('No session is supplied')
            raise exc.HTTPUnauthorized
        return func(self, request, *args, **kwargs)
    return __inner


