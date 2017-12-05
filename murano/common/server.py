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

import uuid

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
from oslo_messaging.rpc import dispatcher
from oslo_messaging import target
from oslo_service import service
from oslo_utils import timeutils
import pytz
from sqlalchemy import desc

from murano.common.helpers import token_sanitizer
from murano.db import models
from murano.db.services import environments
from murano.db.services import instances
from murano.db import session
from murano.engine.system import status_reporter
from murano.services import states

CONF = cfg.CONF

LOG = logging.getLogger(__name__)


class ResultEndpoint(object):
    @staticmethod
    def process_result(context, result, environment_id):
        secure_result = token_sanitizer.TokenSanitizer().sanitize(result)
        LOG.debug('Got result from orchestration '
                  'engine:\n{result}'.format(result=secure_result))

        model = result['model']
        action_result = result.get('action', {})

        unit = session.get_session()
        environment = unit.query(models.Environment).get(environment_id)

        if not environment:
            LOG.warning('Environment result could not be handled, '
                        'specified environment not found in database')
            return

        if model['Objects'] is None and model.get('ObjectsCopy', {}) is None:
            environments.EnvironmentServices.remove(environment_id)
            return

        environment.description = model
        if environment.description['Objects'] is not None:
            environment.description['Objects']['services'] = \
                environment.description['Objects'].pop('applications', [])
            action_name = 'Deployment'
            deleted = False
        else:
            action_name = 'Deletion'
            deleted = True
        environment.version += 1
        environment.save(unit)

        # close deployment
        deployment = get_last_deployment(unit, environment.id)
        deployment.finished = timeutils.utcnow()
        deployment.result = action_result

        num_errors = unit.query(models.Status)\
            .filter_by(level='error', task_id=deployment.id).count()
        num_warnings = unit.query(models.Status)\
            .filter_by(level='warning', task_id=deployment.id).count()

        final_status_text = action_name + ' finished'
        if num_errors:
            final_status_text += " with errors"

        elif num_warnings:
            final_status_text += " with warnings"

        status = models.Status()
        status.task_id = deployment.id
        status.text = final_status_text
        status.level = 'info'
        deployment.statuses.append(status)
        deployment.save(unit)

        # close session
        conf_session = unit.query(models.Session).filter_by(
            **{'environment_id': environment.id,
               'state': states.SessionState.DEPLOYING if not deleted
               else states.SessionState.DELETING}).first()
        if num_errors > 0 or result['action'].get('isException'):
            conf_session.state = \
                states.SessionState.DELETE_FAILURE if deleted else \
                states.SessionState.DEPLOY_FAILURE
        else:
            conf_session.state = states.SessionState.DEPLOYED
        conf_session.save(unit)

        # output application tracking information
        services = []
        objects = model['Objects']
        if objects:
            services = objects.get('services')
        if num_errors + num_warnings > 0:
            LOG.warning('EnvId: {env_id} TenantId: {tenant_id} Status: '
                        'Failed Apps: {services}'
                        .format(env_id=environment.id,
                                tenant_id=environment.tenant_id,
                                services=services))
        else:
            LOG.info('EnvId: {env_id} TenantId: {tenant_id} Status: '
                     'Successful Apps: {services}'
                     .format(env_id=environment.id,
                             tenant_id=environment.tenant_id,
                             services=services))
            if action_name == 'Deployment':
                env = environment.to_dict()
                env["deployment_started"] = deployment.started
                env["deployment_finished"] = deployment.finished
                status_reporter.get_notifier().report(
                    'environment.deploy.end', env)


def notification_endpoint_wrapper(priority='info'):
    def wrapper(func):
        class NotificationEndpoint(object):
            def __init__(self):
                setattr(self, priority, self._handler)

            def _handler(self, ctxt, publisher_id, event_type,
                         payload, metadata):
                if event_type == ('murano.%s' % func.__name__):
                    func(payload)

            def __call__(self, payload):
                return func(payload)
        return NotificationEndpoint()
    return wrapper


@notification_endpoint_wrapper()
def track_instance(payload):
    LOG.debug('Got track instance request from orchestration '
              'engine:\n{payload}'.format(payload=payload))
    instance_id = payload['instance']
    instance_type = payload.get('instance_type', 0)
    environment_id = payload['environment']
    unit_count = payload.get('unit_count')
    type_name = payload['type_name']
    type_title = payload.get('type_title')

    instances.InstanceStatsServices.track_instance(
        instance_id, environment_id, instance_type,
        type_name, type_title, unit_count)


@notification_endpoint_wrapper()
def untrack_instance(payload):
    LOG.debug('Got untrack instance request from orchestration '
              'engine:\n{payload}'.format(payload=payload))
    instance_id = payload['instance']
    environment_id = payload['environment']
    instances.InstanceStatsServices.destroy_instance(
        instance_id, environment_id)


@notification_endpoint_wrapper()
def report_notification(report):
    LOG.debug('Got report from orchestration '
              'engine:\n{report}'.format(report=report))

    report['entity_id'] = report.pop('id')

    status = models.Status()
    if 'timestamp' in report:
        dt = timeutils.parse_isotime(report.pop('timestamp'))
        report['created'] = dt.astimezone(pytz.utc).replace(tzinfo=None)
    status.update(report)

    unit = session.get_session()
    # connect with deployment
    with unit.begin():
        running_deployment = get_last_deployment(unit,
                                                 status.environment_id)
        status.task_id = running_deployment.id
        unit.add(status)


def get_last_deployment(unit, env_id):
    query = unit.query(models.Task) \
        .filter_by(environment_id=env_id) \
        .order_by(desc(models.Task.started))
    return query.first()


class Service(service.Service):
    """Service class, that contains common methods for custom services"""

    def __init__(self):
        super(Service, self).__init__()
        self.server = None

    def stop(self, graceful=False):
        if self.server:
            self.server.stop()
            if graceful:
                self.server.wait()
        super(Service, self).stop()

    def reset(self):
        if self.server:
            self.server.reset()
        super(Service, self).reset()


def get_notification_listener():

    endpoints = [report_notification, track_instance, untrack_instance]
    transport = messaging.get_notification_transport(CONF)
    s_target = target.Target(topic='murano', server=str(uuid.uuid4()))
    listener = messaging.get_notification_listener(
        transport, [s_target], endpoints, executor='threading')

    return listener


def get_rpc_server():

    endpoints = [ResultEndpoint()]
    transport = messaging.get_rpc_transport(CONF)
    s_target = target.Target('murano', 'results', server=str(uuid.uuid4()))
    access_policy = dispatcher.DefaultRPCAccessPolicy
    server = messaging.get_rpc_server(
        transport, s_target, endpoints, 'threading',
        access_policy=access_policy)

    return server


class NotificationService(Service):
    def __init__(self):
        super(NotificationService, self).__init__()
        self.server = None

    def start(self):
        endpoints = [report_notification, track_instance, untrack_instance]

        transport = messaging.get_notification_transport(CONF)
        s_target = target.Target(topic='murano', server=str(uuid.uuid4()))

        self.server = messaging.get_notification_listener(
            transport, [s_target], endpoints, executor='eventlet')

        self.server.start()
        super(NotificationService, self).start()


class ApiService(Service):

    def start(self):
        endpoints = [ResultEndpoint()]

        transport = messaging.get_rpc_transport(CONF)
        s_target = target.Target('murano', 'results', server=str(uuid.uuid4()))
        access_policy = dispatcher.DefaultRPCAccessPolicy
        self.server = messaging.get_rpc_server(
            transport, s_target, endpoints, 'eventlet',
            access_policy=access_policy)
        self.server.start()
        super(ApiService, self).start()
