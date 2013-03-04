from portas.db.api import EnvironmentRepository
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

        return self.repository.add(params).to_dict()


def create_resource():
    return wsgi.Resource(Controller())