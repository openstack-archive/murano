from amqplib.client_0_8 import Message
import anyjson
import eventlet
from eventlet.semaphore import Semaphore
from webob import exc
from portas.common import config
from portas.db.models import Session, Status, Environment
from portas.db.session import get_session
from portas.openstack.common import wsgi
from portas.openstack.common import log as logging

amqp = eventlet.patcher.import_patched('amqplib.client_0_8')
rabbitmq = config.CONF.rabbitmq
log = logging.getLogger(__name__)


class Controller(object):
    def __init__(self):
        self.write_lock = Semaphore(1)
        connection = amqp.Connection('{0}:{1}'.format(rabbitmq.host, rabbitmq.port), virtual_host=rabbitmq.virtual_host,
                                     userid=rabbitmq.userid, password=rabbitmq.password,
                                     ssl=rabbitmq.use_ssl, insist=True)
        self.ch = connection.channel()
        self.ch.exchange_declare('tasks', 'direct', durable=True, auto_delete=False)

    def index(self, request, environment_id):
        log.debug(_('Session:List <EnvId: {0}>'.format(environment_id)))


        filters = {'environment_id': environment_id, 'user_id': request.context.user}

        unit = get_session()
        configuration_sessions = unit.query(Session).filter_by(**filters)

        return {"sessions": [session.to_dict() for session in configuration_sessions if
                             session.environment.tenant_id == request.context.tenant]}

    def configure(self, request, environment_id):
        log.debug(_('Session:Configure <EnvId: {0}>'.format(environment_id)))

        params = {'environment_id': environment_id, 'user_id': request.context.user, 'state': 'open'}

        session = Session()
        session.update(params)

        unit = get_session()
        if unit.query(Session).filter_by(**{'environment_id': environment_id, 'state': 'open'}).first():
            log.info('There is already open session for this environment')
            raise exc.HTTPConflict

        #create draft for apply later changes
        environment = unit.query(Environment).get(environment_id)
        session.description = environment.description

        with unit.begin():
            unit.add(session)

        return session.to_dict()

    def show(self, request, environment_id, session_id):
        log.debug(_('Session:Show <EnvId: {0}, SessionId: {1}>'.format(environment_id, session_id)))

        unit = get_session()
        session = unit.query(Session).get(session_id)

        if session.environment.tenant_id != request.context.tenant:
            log.info('User is not authorized to access this tenant resources.')
            raise exc.HTTPUnauthorized

        return session.to_dict()

    def delete(self, request, environment_id, session_id):
        log.debug(_('Session:Delete <EnvId: {0}, SessionId: {1}>'.format(environment_id, session_id)))

        unit = get_session()
        session = unit.query(Session).get(session_id)

        if session.state == 'deploying':
            log.info('Session is in \'deploying\' state. Could not be deleted.')
            raise exc.HTTPForbidden(comment='Session object in \'deploying\' state could not be deleted')

        with unit.begin():
            unit.delete(session)

        return None

    def reports(self, request, environment_id, session_id):
        log.debug(_('Session:Reports <EnvId: {0}, SessionId: {1}>'.format(environment_id, session_id)))

        unit = get_session()
        statuses = unit.query(Status).filter_by(session_id=session_id)

        return {'reports': [status.to_dict() for status in statuses]}

    def deploy(self, request, environment_id, session_id):
        log.debug(_('Session:Deploy <EnvId: {0}, SessionId: {1}>'.format(environment_id, session_id)))

        unit = get_session()
        session = unit.query(Session).get(session_id)

        if session.state != 'open':
            log.warn(_('Could not deploy session. Session is already deployed or in deployment state'))

        session.state = 'deploying'
        session.save(unit)

        with self.write_lock:
            self.ch.basic_publish(Message(body=anyjson.serialize(session.description)), 'tasks', 'tasks')


def create_resource():
    return wsgi.Resource(Controller())