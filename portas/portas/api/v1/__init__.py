from portas.db.models import Session
from portas.db.session import get_session


def get_draft(session_id):
    unit = get_session()
    session = unit.query(Session).get(session_id)

    return session.description


def save_draft(session_id, draft):
    unit = get_session()
    session = unit.query(Session).get(session_id)

    session.description = draft
    session.save(unit)