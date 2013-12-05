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
from muranocommon.helpers.token_sanitizer import TokenSanitizer
from muranocommon.messaging import MqClient
from sqlalchemy import desc
import eventlet

conf = config.CONF.reports
log = logging.getLogger(__name__)


class TaskResultHandlerService(service.Service):
    def __init__(self):
        super(TaskResultHandlerService, self).__init__()

    def start(self):
        super(TaskResultHandlerService, self).start()
        self.tg.add_thread(self._handle_results)
        self.tg.add_thread(self._handle_reports)

    def stop(self):
        super(TaskResultHandlerService, self).stop()

    def _create_mq_client(self):
        rabbitmq = config.CONF.rabbitmq
        connection_params = {
            'login': rabbitmq.login,
            'password': rabbitmq.password,
            'host': rabbitmq.host,
            'port': rabbitmq.port,
            'virtual_host': rabbitmq.virtual_host,
            'ssl': rabbitmq.ssl,
            'ca_certs': rabbitmq.ca_certs.strip() or None
        }
        return MqClient(**connection_params)

    def _handle_results(self):
        reconnect_delay = 1
        while True:
            try:
                with self._create_mq_client() as mqClient:
                    mqClient.declare(conf.results_exchange, conf.results_queue,
                                     enable_ha=True)
                    with mqClient.open(conf.results_queue,
                                       prefetch_count=100) as results_sb:
                        reconnect_delay = 1
                        while True:
                            result = results_sb.get_message(timeout=1)
                            if result:
                                eventlet.spawn(handle_result, result)
            except Exception as ex:
                log.exception(ex)

                eventlet.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 60)

    def _handle_reports(self):
        reconnect_delay = 1
        while True:
            try:
                with self._create_mq_client() as mqClient:
                    mqClient.declare(conf.reports_exchange, conf.reports_queue,
                                     enable_ha=True)
                    with mqClient.open(conf.reports_queue,
                                       prefetch_count=100) as reports_sb:
                        reconnect_delay = 1
                        while True:
                            report = reports_sb.get_message(timeout=1)
                            if report:
                                eventlet.spawn(handle_report, report)
            except Exception as ex:
                log.exception(ex)

                eventlet.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, 60)


@handle
def handle_result(message):
    try:
        environment_result = message.body
        secure_result = TokenSanitizer().sanitize(environment_result)
        log.debug(_('Got result message from '
                    'orchestration engine:\n{0}'.format(secure_result)))

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
        environment.networking = environment_result.get('networking', {})
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

        num_errors = session.query(Status).filter_by(level='error',
                                                     deployment_id=deployment.
                                                     id).count()
        num_warnings = session.query(Status).filter_by(level='warning',
                                                       deployment_id=
                                                       deployment.id).count()

        final_status_text = "Deployment finished"
        if num_errors:
            final_status_text += " with errors"

        elif num_warnings:
            final_status_text += " with warnings"

        status = Status()
        status.deployment_id = deployment.id
        status.text = final_status_text
        status.level = 'info'
        deployment.statuses.append(status)
        deployment.save(session)
    except Exception as ex:
        log.exception(ex)
    finally:
        message.ack()


@handle
def handle_report(message):
    try:
        report = message.body
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
    except Exception as ex:
        log.exception(ex)
    finally:
        message.ack()


def get_last_deployment(session, env_id):
    query = session.query(Deployment). \
        filter_by(environment_id=env_id). \
        order_by(desc(Deployment.started))
    return query.first()
