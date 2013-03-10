from portas import utils
from portas.common import uuidutils
from portas.db.models import Session
from portas.db.session import get_session
from portas.openstack.common import wsgi, timeutils
from portas.openstack.common import log as logging

log = logging.getLogger(__name__)


class Controller(object):
    @utils.verify_session
    def index(self, request, environment_id):
        draft = get_draft(request.context.session)

        if not draft.has_key('services'):
            return dict()

        if not draft['services'].has_key('activeDirectories'):
            return dict()

        return {'activeDirectories': draft['services']['activeDirectories']}

    @utils.verify_session
    def create(self, request, environment_id, body):
        draft = get_draft(request.context.session)

        active_directory = body.copy()
        active_directory['id'] = uuidutils.generate_uuid()
        active_directory['created'] = timeutils.utcnow
        active_directory['updated'] = timeutils.utcnow

        for unit in active_directory['units']:
            unit['id'] = uuidutils.generate_uuid()

        draft = prepare_draft(draft)
        draft['services']['activeDirectories'].append(active_directory)
        save_draft(request.context.session, draft)

        return active_directory

    def delete(self, request, environment_id, active_directory_id):
        draft = get_draft(request.context.session)
        draft['services']['activeDirectories'] = [service for service in draft['services']['activeDirectories'] if
                                                  service['id'] != active_directory_id]
        save_draft(request.context.session, draft)


def get_draft(session_id):
    unit = get_session()
    session = unit.query(Session).get(session_id)

    return session.description


def save_draft(session_id, draft):
    unit = get_session()
    session = unit.query(Session).get(session_id)

    session.description = draft
    session.save(unit)


def prepare_draft(draft):
    if not draft.has_key('services'):
        draft['services'] = {}

    if not draft['services'].has_key('activeDirectories'):
        draft['services']['activeDirectories'] = []

    return draft


def create_resource():
    return wsgi.Resource(Controller())