import contextlib
import functools
import logging
import sys

import webob.exc

LOG = logging.getLogger(__name__)


def http_success_code(code):
    """Attaches response code to a method.

    This decorator associates a response code with a method.  Note
    that the function attributes are directly manipulated; the method
    is not wrapped.
    """

    def decorator(func):
        func.wsgi_code = code
        return func
    return decorator


def verify_tenant(func):
    @functools.wraps(func)
    def __inner(self, req, tenant_id, *args, **kwargs):
        if hasattr(req, 'context') and tenant_id != req.context.tenant_id:
            LOG.info('User is not authorized to access this tenant.')
            raise webob.exc.HTTPUnauthorized
        return func(self, req, tenant_id, *args, **kwargs)
    return __inner


def require_admin(func):
    @functools.wraps(func)
    def __inner(self, req, *args, **kwargs):
        if hasattr(req, 'context') and not req.context.is_admin:
            LOG.info('User has no admin priviledges.')
            raise webob.exc.HTTPUnauthorized
        return func(self, req, *args, **kwargs)
    return __inner


@contextlib.contextmanager
def save_and_reraise_exception():
    """Save current exception, run some code and then re-raise.

    In some cases the exception context can be cleared, resulting in None
    being attempted to be reraised after an exception handler is run. This
    can happen when eventlet switches greenthreads or when running an
    exception handler, code raises and catches an exception. In both
    cases the exception context will be cleared.

    To work around this, we save the exception state, run handler code, and
    then re-raise the original exception. If another exception occurs, the
    saved exception is logged and the new exception is reraised.
    """
    type_, value, traceback = sys.exc_info()
    try:
        yield
    except Exception:
        LOG.error('Original exception being dropped',
                  exc_info=(type_, value, traceback))
        raise
    raise type_, value, traceback
