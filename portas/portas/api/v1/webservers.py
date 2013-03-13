from portas import utils
from portas.api.v1 import save_draft, get_draft, get_service_status
from portas.common import uuidutils
from portas.openstack.common import wsgi, timeutils
from portas.openstack.common import log as logging

log = logging.getLogger(__name__)


class Controller(object):
    def index(self, request, environment_id):
        log.debug(_('WebServer:List <EnvId: {0}>'.format(environment_id)))

        draft = prepare_draft(get_draft(environment_id, request.context.session))

        for dc in draft['services']['webServers']:
            dc['status'] = get_service_status(environment_id, request.context.session, dc)

        return {'webServers': draft['services']['webServers']}

    @utils.verify_session
    def create(self, request, environment_id, body):
        log.debug(_('WebServer:Create <EnvId: {0}, Body: {1}>'.format(environment_id, body)))

        draft = get_draft(session_id=request.context.session)

        webServer = body.copy()
        webServer['id'] = uuidutils.generate_uuid()
        webServer['created'] = str(timeutils.utcnow())
        webServer['updated'] = str(timeutils.utcnow())

        unit_count = 0
        for unit in webServer['units']:
            unit_count += 1
            unit['id'] = uuidutils.generate_uuid()
            unit['name'] = 'iis{0}{1}'.format(unit_count, webServer['id'][:3])

        draft = prepare_draft(draft)
        draft['services']['webServers'].append(webServer)
        save_draft(request.context.session, draft)

        return webServer

    @utils.verify_session
    def delete(self, request, environment_id, web_server_id):
        log.debug(_('WebServer:Delete <EnvId: {0}, Id: {1}>'.format(environment_id, web_server_id)))

        draft = get_draft(session_id=request.context.session)
        draft['services']['webServers'] = [service for service in draft['services']['webServers'] if
                                           service['id'] != web_server_id]
        save_draft(request.context.session, draft)


def prepare_draft(draft):
    if not draft.has_key('services'):
        draft['services'] = {}

    if not draft['services'].has_key('webServers'):
        draft['services']['webServers'] = []

    return draft


def create_resource():
    return wsgi.Resource(Controller())