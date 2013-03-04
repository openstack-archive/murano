import logging

LOG = logging.getLogger(__name__)


# def verify_tenant(func):
#     @functools.wraps(func)
#     def __inner(self, req, tenant_id, *args, **kwargs):
#         if hasattr(req, 'context') and tenant_id != req.context.tenant:
#             LOG.info('User is not authorized to access this tenant.')
#             raise webob.exc.HTTPUnauthorized
#         return func(self, req, tenant_id, *args, **kwargs)
#     return __inner
#
#
# def require_admin(func):
#     @functools.wraps(func)
#     def __inner(self, req, *args, **kwargs):
#         if hasattr(req, 'context') and not req.context.is_admin:
#             LOG.info('User has no admin priviledges.')
#             raise webob.exc.HTTPUnauthorized
#         return func(self, req, *args, **kwargs)
#     return __inner

