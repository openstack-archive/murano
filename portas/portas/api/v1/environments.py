from webob import exc
from portas.db.api import EnvironmentRepository
from portas.db.models import Environment
from portas.openstack.common import wsgi
from portas.openstack.common import log as logging


log = logging.getLogger(__name__)


class Controller(object):
    repository = EnvironmentRepository()

    def index(self, request):
        log.debug(_("Display list of environments"))

        #Only environments from same tenant as users should be shown
        filters = {'tenant_id': request.context.tenant}
        return {"environments": [env.to_dict() for env in self.repository.list(filters)]}

    def create(self, request, body):
        params = body.copy()
        params['tenant_id'] = request.context.tenant

        env = Environment()
        env.update(params)

        return self.repository.add(env).to_dict()

    def show(self, request, environment_id):
        environment = self.repository.get(environment_id)

        if environment.tenant_id != request.context.tenant:
            log.info('User is not authorized to access this tenant resources.')
            raise exc.HTTPUnauthorized

        return environment.to_dict()

    def update(self, request, environment_id, body):
        environment = self.repository.get(environment_id)

        if environment.tenant_id != request.context.tenant:
            log.info('User is not authorized to access this tenant resources.')
            raise exc.HTTPUnauthorized

        environment.update(body)
        environment.save()

        return environment.to_dict()

    def delete(self, request, environment_id):
        environment = self.repository.get(environment_id)
        self.repository.remove(environment)

        return None


def create_resource():
    return wsgi.Resource(Controller())