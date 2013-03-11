from portas import utils
from portas.api.v1 import save_draft, get_draft
from portas.common import uuidutils
from portas.openstack.common import wsgi, timeutils
from portas.openstack.common import log as logging

log = logging.getLogger(__name__)


class Controller(object):
    @utils.verify_session
    def index(self, request, environment_id):
        draft = get_draft(request.context.session)

        if not draft.has_key('services'):
            return dict()

        if not draft['services'].has_key('webServers'):
            return dict()

        return {'webServers': draft['services']['webServers']}

    @utils.verify_session
    def create(self, request, environment_id, body):
        draft = get_draft(request.context.session)

        webServer = body.copy()
        webServer['id'] = uuidutils.generate_uuid()
        webServer['created'] = timeutils.utcnow
        webServer['updated'] = timeutils.utcnow

        unit_count = 0
        for unit in webServer['units']:
            unit_count += 1
            unit['id'] = uuidutils.generate_uuid()
            unit['name'] = 'iis{0}'.format(unit_count)

        draft = prepare_draft(draft)
        draft['services']['webServers'].append(webServer)
        save_draft(request.context.session, draft)

        return webServer

    @utils.verify_session
    def delete(self, request, environment_id, web_server_id):
        draft = get_draft(request.context.session)
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