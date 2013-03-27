from amqplib.client_0_8 import Message
import anyjson
import eventlet
from webob import exc
from portas.common import config
from portas.api.v1 import get_env_status
from portas.db.session import get_session
from portas.db.models import Environment
from portas.openstack.common import wsgi
from portas.openstack.common import log as logging

amqp = eventlet.patcher.import_patched('amqplib.client_0_8')
rabbitmq = config.CONF.rabbitmq

log = logging.getLogger(__name__)


class Controller(object):
    def index(self, request):
        log.debug(_('Environments:List'))

        #Only environments from same tenant as users should be shown
        filters = {'tenant_id': request.context.tenant}

        session = get_session()
        environments = session.query(Environment).filter_by(**filters)
        environments = [env.to_dict() for env in environments]

        for env in environments:
            env['status'] = get_env_status(env['id'], request.context.session)

        return {"environments": environments}

    def create(self, request, body):
        log.debug(_('Environments:Create <Body {0}>'.format(body)))

        #tagging environment by tenant_id for later checks
        params = body.copy()
        params['tenant_id'] = request.context.tenant

        environment = Environment()
        environment.update(params)

        session = get_session()
        with session.begin():
            session.add(environment)

        #saving environment as Json to itself
        environment.update({"description": environment.to_dict()})
        environment.save(session)

        return environment.to_dict()

    def show(self, request, environment_id):
        log.debug(_('Environments:Show <Id: {0}>'.format(environment_id)))

        session = get_session()
        environment = session.query(Environment).get(environment_id)

        if environment.tenant_id != request.context.tenant:
            log.info('User is not authorized to access this tenant resources.')
            raise exc.HTTPUnauthorized

        env = environment.to_dict()
        env['status'] = get_env_status(environment_id, request.context.session)

        return env

    def update(self, request, environment_id, body):
        log.debug(_('Environments:Update <Id: {0}, Body: {1}>'.
                    format(environment_id, body)))

        session = get_session()
        environment = session.query(Environment).get(environment_id)

        if environment.tenant_id != request.context.tenant:
            log.info('User is not authorized to access this tenant resources.')
            raise exc.HTTPUnauthorized

        environment.update(body)
        environment.save(session)

        return environment.to_dict()

    def delete(self, request, environment_id):
        log.debug(_('Environments:Delete <Id: {0}>'.format(environment_id)))

        session = get_session()
        environment = session.query(Environment).get(environment_id)

        with session.begin():
            session.delete(environment)

        #preparing data for removal from conductor
        env = environment.description
        env['services'] = []
        env['deleted'] = True
        #Set X-Auth-Token for conductor
        env['token'] = request.context.auth_token

        connection = amqp.Connection('{0}:{1}'.
                                     format(rabbitmq.host, rabbitmq.port),
                                     virtual_host=rabbitmq.virtual_host,
                                     userid=rabbitmq.userid,
                                     password=rabbitmq.password,
                                     ssl=rabbitmq.use_ssl, insist=True)
        channel = connection.channel()
        channel.exchange_declare('tasks', 'direct', durable=True,
                                 auto_delete=False)

        channel.basic_publish(Message(body=anyjson.serialize(env)), 'tasks',
                              'tasks')

        return None


def create_resource():
    return wsgi.Resource(Controller())
