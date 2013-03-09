from webob import exc
from portas.db.models import Session
from portas.db.session import get_session
from portas.openstack.common import wsgi
from portas.openstack.common import log as logging


log = logging.getLogger(__name__)


class Controller(object):
    def index(self, request, environment_id):
        filters = {'environment_id': environment_id, 'user_id': request.context.user}

        unit = get_session()
        configuration_sessions = unit.query(Session).filter_by(**filters)

        return {"sessions": [session.to_dict() for session in configuration_sessions if
                             session.environment.tenant_id == request.context.tenant]}

    def configure(self, request, environment_id):
        params = {'environment_id': environment_id, 'user_id': request.context.user, 'state': 'open'}

        session = Session()
        session.update(params)

        unit = get_session()
        if unit.query(Session).filter_by(**{'environment_id': environment_id, 'state': 'open'}).first():
            log.info('There is already open session for this environment')
            raise exc.HTTPConflict

        with unit.begin():
            unit.add(session)

        return session.to_dict()

    def show(self, request, environment_id, session_id):
        unit = get_session()
        session = unit.query(Session).get(session_id)

        if session.environment.tenant_id != request.context.tenant:
            log.info('User is not authorized to access this tenant resources.')
            raise exc.HTTPUnauthorized

        return session.to_dict()

    def delete(self, request, environment_id, session_id):
        unit = get_session()
        session = unit.query(Session).get(session_id)

        if session.state == 'deploying':
            log.info('Session is in \'deploying\' state. Could not be deleted.')
            raise exc.HTTPForbidden(comment='Session object in \'deploying\' state could not be deleted')

        with unit.begin():
            unit.delete(session)

        return None

    def deploy(self, request, environment_id, session_id):
        log.debug(_("Got Deploy command"))


def create_resource():
    return wsgi.Resource(Controller())