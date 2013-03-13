from portas.db.models import Session, Environment, Status
from portas.db.session import get_session


def get_draft(environment_id=None, session_id=None):
    unit = get_session()
    #TODO: When session is deployed should be returned env.description
    if session_id:
        session = unit.query(Session).get(session_id)
        return session.description
    else:
        environment = unit.query(Environment).get(environment_id)
        return environment.description


def save_draft(session_id, draft):
    unit = get_session()
    session = unit.query(Session).get(session_id)

    session.description = draft
    session.save(unit)


def get_env_status(environment_id, session_id):
    status = 'draft'

    if not session_id:
        return status

    unit = get_session()
    session_state = unit.query(Session).get(session_id).state
    reports_count = unit.query(Status).filter_by(environment_id=environment_id, session_id=session_id).count()

    if session_state == 'deployed':
        status = 'finished'

    if session_state == 'deploying' and reports_count > 1:
        status = 'pending'

    draft = get_draft(environment_id, session_id)

    if not 'services' in draft:
        return 'pending'

    def get_statuses(type):
        if type in draft['services']:
            return [get_service_status(environment_id, session_id, service) for service in
                    draft['services'][type]]
        else:
            return []

    is_inprogress = filter(lambda item: item == 'inprogress',
                           get_statuses('activeDirectories') + get_statuses('webServers'))

    if session_state == 'deploying' and is_inprogress > 1:
        status = 'inprogress'

    return status


def get_service_status(environment_id, session_id, service):
    status = 'draft'

    unit = get_session()
    session_state = unit.query(Session).get(session_id).state

    entities = [u['id'] for u in service['units']]
    reports_count = unit.query(Status).filter(Status.environment_id == environment_id
                                              and Status.session_id == session_id
                                              and Status.entity_id.in_(entities))\
                                      .count()

    if session_state == 'deployed':
        status = 'finished'

    if session_state == 'deploying' and reports_count == 0:
        status = 'pending'

    if session_state == 'deploying' and reports_count > 0:
        status = 'inprogress'

    return status
