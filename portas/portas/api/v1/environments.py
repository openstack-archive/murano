from portas.db.api import EnvironmentRepository
from portas.openstack.common import wsgi
from portas.openstack.common import log as logging


log = logging.getLogger(__name__)


class Controller(object):
    repository = EnvironmentRepository()

    def index(self, request):
        log.debug(_("Display list of environments"))
        return {"environments": [env.to_dict() for env in self.repository.list()]}

    def create(self, request, body):
        params = body.copy()
        params['tenant_id'] = request.context.tenant

        return self.repository.add(params).to_dict()

    # def delete(self, request, datacenter_id):
    #     log.debug("Got delete request. Request: %s", req)
    #     self.repository., datacenter_id)
    #
    # def update(self, req, tenant_id, datacenter_id, body):
    #     log.debug("Got update request. Request: %s", req)
    #     core_api.update_dc(self.conf, tenant_id, datacenter_id, body)
    #     return {'datacenter': {'id': dc_id}}


def create_resource():
    return wsgi.Resource(Controller())