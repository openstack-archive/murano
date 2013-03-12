from portas.db.models import Session, Environment
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