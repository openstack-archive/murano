#    Copyright (c) 2013 Mirantis, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from muranoapi.common.utils import handle
from muranoapi.db.models import Status, Session, Environment, Deployment
from muranoapi.db.session import get_session
from muranoapi.openstack.common import log as logging, timeutils, service
from muranoapi.common import config
from muranocommon.mq import MqClient
from sqlalchemy import desc

conf = config.CONF.reports
rabbitmq = config.CONF.rabbitmq
log = logging.getLogger(__name__)


class TaskResultHandlerService(service.Service):
    connection_params = {
        'login': rabbitmq.login,
        'password': rabbitmq.password,
        'host': rabbitmq.host,
        'port': rabbitmq.port,
        'virtual_host': rabbitmq.virtual_host
    }

    def __init__(self):
        super(TaskResultHandlerService, self).__init__()

    def start(self):
        super(TaskResultHandlerService, self).start()
        self.tg.add_thread(self._start_rabbitmq)

    def stop(self):
        super(TaskResultHandlerService, self).stop()

    def _start_rabbitmq(self):
        while True:
            try:
                with MqClient(**self.connection_params) as mqClient:
                    mqClient.declare(conf.results_exchange, conf.results_queue)
                    mqClient.declare(conf.reports_exchange, conf.reports_queue)
                    with mqClient.open(conf.results_queue) as results_sb:
                        with mqClient.open(conf.reports_queue) as reports_sb:
                            while True:
                                report = reports_sb.get_message(timeout=1000)
                                self.tg.add_thread(handle_report, report.body)
                                result = results_sb.get_message(timeout=1000)
                                self.tg.add_thread(handle_result, result.body)
            except Exception as ex:
                log.exception(ex)


@handle
def handle_result(environment_result):
    log.debug(_('Got result message from '
                'orchestration engine:\n{0}'.format(environment_result)))

    if 'deleted' in environment_result:
        log.debug(_('Result for environment {0} is dropped. Environment '
                    'is deleted'.format(environment_result['id'])))
        return

    session = get_session()
    environment = session.query(Environment).get(environment_result['id'])

    if not environment:
        log.warning(_('Environment result could not be handled, specified '
                      'environment does not found in database'))
        return

    environment.description = environment_result
    environment.version += 1
    environment.save(session)

    #close session
    conf_session = session.query(Session).filter_by(
        **{'environment_id': environment.id, 'state': 'deploying'}).first()
    conf_session.state = 'deployed'
    conf_session.save(session)

    #close deployment
    deployment = get_last_deployment(session, environment.id)
    deployment.finished = timeutils.utcnow()
    status = Status()
    status.deployment_id = deployment.id
    status.text = "Deployment finished"
    deployment.statuses.append(status)
    deployment.save(session)


@handle
def handle_report(report):
    log.debug(_('Got report message from orchestration '
                'engine:\n{0}'.format(report)))

    report['entity_id'] = report['id']
    del report['id']

    status = Status()
    status.update(report)

    session = get_session()
    #connect with deployment
    with session.begin():
        running_deployment = get_last_deployment(session,
                                                 status.environment_id)
        status.deployment_id = running_deployment.id
        session.add(status)


def get_last_deployment(session, env_id):
    query = session.query(Deployment). \
        filter_by(environment_id=env_id). \
        order_by(desc(Deployment.started))
    return query.first()
