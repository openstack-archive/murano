from webob import exc
from portas.db.api import SessionRepository
from portas.db.models import Session
from portas.openstack.common import wsgi
from portas.openstack.common import log as logging


log = logging.getLogger(__name__)


class Controller(object):
    repository = SessionRepository()

    def index(self, request, environment_id):
        filters = {'environment_id': environment_id, 'user_id': request.context.user,
                   'environment.tenant_id': request.context.tenant}
        return {"sessions": [session.to_dict() for session in self.repository.list(filters)]}

    def configure(self, request, environment_id):
        params = {'environment_id': environment_id, 'user_id': request.context.user, 'state': 'open'}

        session = Session()
        session.update(params)

        if self.repository.list({'environment_id': environment_id, 'state': 'open'}):
            log.info('There is already open session for this environment')
            raise exc.HTTPConflict

        return self.repository.add(session).to_dict()

    def show(self, request, environment_id, session_id):
        session = self.repository.get(session_id)

        if session.environment.tenant_id != request.context.tenant:
            log.info('User is not authorized to access this tenant resources.')
            raise exc.HTTPUnauthorized

        return session.to_dict()

    def delete(self, request, environment_id, session_id):
        session = self.repository.get(session_id)

        if session.state == 'deploying':
            log.info('Session is in \'deploying\' state. Could not be deleted.')
            raise exc.HTTPForbidden(comment='Session object in \'deploying\' state could not be deleted')

        self.repository.remove(session)

        return None


def create_resource():
    return wsgi.Resource(Controller())