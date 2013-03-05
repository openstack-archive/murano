from portas.db.models import Environment, Session
from portas.db.session import get_session


class EnvironmentRepository(object):
    def list(self, filters=None):
        session = get_session()
        query = session.query(Environment)

        if filters:
            query = query.filter_by(**filters)

        return query.all()

    def add(self, environment):
        session = get_session()
        with session.begin():
            session.add(environment)
            return environment

    def get(self, environment_id):
        session = get_session()

        query = session.query(Environment)
        query = query.filter(Environment.id == environment_id)

        return query.first()

    def remove(self, environment):
        session = get_session()
        with session.begin():
            session.delete(environment)


class SessionRepository(object):
    def list(self, filters=None):
        session = get_session()
        query = session.query(Session)

        if filters:
            query = query.filter_by(**filters)

        return query.all()

    def add(self, session):
        s = get_session()
        with s.begin():
            s.add(session)
            return session

    def get(self, session_id):
        session = get_session()

        query = session.query(Session)

        return query.get(session_id)

    def remove(self, session):
        s = get_session()
        with s.begin():
            s.delete(session)