from portas import utils
from portas.api.v1 import save_draft, get_draft
from portas.common import uuidutils
from portas.openstack.common import wsgi, timeutils
from portas.openstack.common import log as logging

log = logging.getLogger(__name__)


class Controller(object):
    @utils.verify_session
    def index(self, request, environment_id):
        log.debug(_('ActiveDirectory:Index <EnvId: {0}}>'.format(environment_id)))

        draft = get_draft(request.context.session)

        if not draft.has_key('services'):
            return dict()

        if not draft['services'].has_key('activeDirectories'):
            return dict()

        return {'activeDirectories': draft['services']['activeDirectories']}

    @utils.verify_session
    def create(self, request, environment_id, body):
        log.debug(_('ActiveDirectory:Create <EnvId: {0}, Body: {1}>'.format(environment_id, body)))

        draft = get_draft(request.context.session)

        active_directory = body.copy()
        active_directory['id'] = uuidutils.generate_uuid()
        active_directory['created'] = timeutils.utcnow
        active_directory['updated'] = timeutils.utcnow

        unit_count = 0
        for unit in active_directory['units']:
            unit_count += 1
            unit['id'] = uuidutils.generate_uuid()
            unit['name'] = 'dc{0}'.format(unit_count)

        draft = prepare_draft(draft)
        draft['services']['activeDirectories'].append(active_directory)
        save_draft(request.context.session, draft)

        return active_directory

    def delete(self, request, environment_id, active_directory_id):
        log.debug(_('ActiveDirectory:Delete <EnvId: {0}, Id: {1}>'.format(environment_id, active_directory_id)))

        draft = get_draft(request.context.session)
        draft['services']['activeDirectories'] = [service for service in draft['services']['activeDirectories'] if
                                                  service['id'] != active_directory_id]
        save_draft(request.context.session, draft)


def prepare_draft(draft):
    if not draft.has_key('services'):
        draft['services'] = {}

    if not draft['services'].has_key('activeDirectories'):
        draft['services']['activeDirectories'] = []

    return draft


def create_resource():
    return wsgi.Resource(Controller())