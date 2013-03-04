from portas.db.models import Environment
from portas.db.session import get_session


class EnvironmentRepository(object):
    def list(self, filters=None):
        session = get_session()
        query = session.query(Environment)

        if filters:
            query = query.filter_by(**filters)

        return query.all()

    def add(self, values):
        session = get_session()
        with session.begin():
            env = Environment()
            env.update(values)
            session.add(env)
            return env