from webob import exc
from portas.db.session import get_session
from portas.db.models import Environment
from portas.openstack.common import wsgi
from portas.openstack.common import log as logging


log = logging.getLogger(__name__)


class Controller(object):
    def index(self, request):
        log.debug(_('Environments:List'))

        #Only environments from same tenant as users should be shown
        filters = {'tenant_id': request.context.tenant}

        session = get_session()
        environments = session.query(Environment).filter_by(**filters)

        return {"environments": [env.to_dict() for env in environments]}

    def create(self, request, body):
        log.debug(_('Environments:Create <Body {0}>'.format(body)))

        #tagging environment by tenant_id for later checks
        params = body.copy()
        params['tenant_id'] = request.context.tenant

        environment = Environment()
        environment.update(params)

        session = get_session()
        with session.begin():
            session.add(environment)

        #saving environment as Json to itself
        environment.update({"description": environment.to_dict()})
        environment.save(session)

        return environment.to_dict()

    def show(self, request, environment_id):
        log.debug(_('Environments:Show <Id: {0}>'.format(environment_id)))

        session = get_session()
        environment = session.query(Environment).get(environment_id)

        if environment.tenant_id != request.context.tenant:
            log.info('User is not authorized to access this tenant resources.')
            raise exc.HTTPUnauthorized

        return environment.to_dict()

    def update(self, request, environment_id, body):
        log.debug(_('Environments:Update <Id: {0}, Body: {1}>'.format(environment_id, body)))

        session = get_session()
        environment = session.query(Environment).get(environment_id)

        if environment.tenant_id != request.context.tenant:
            log.info('User is not authorized to access this tenant resources.')
            raise exc.HTTPUnauthorized

        environment.update(body)
        environment.save(session)

        return environment.to_dict()

    def delete(self, request, environment_id):
        log.debug(_('Environments:Delete <Id: {0}>'.format(environment_id)))

        session = get_session()
        environment = session.query(Environment).get(environment_id)

        with session.begin():
            session.delete(environment)

        return None


def create_resource():
    return wsgi.Resource(Controller())