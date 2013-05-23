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
#    under the License.from oslo.config import cfg

from muranoapi.db.models import Session, Environment, Status
from muranoapi.db.session import get_session


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

    unit = get_session()

    if not session_id:
        variants = ['open', 'deploying']
        session = unit.query(Session).filter(
            Session.environment_id == environment_id and
            Session.state.in_(variants)
        ).first()
        if session:
            session_id = session.id
        else:
            return status

    session_state = unit.query(Session).get(session_id).state
    reports_count = unit.query(Status).filter_by(environment_id=environment_id,
                                                 session_id=session_id).count()

    if session_state == 'deployed':
        status = 'finished'

    if session_state == 'deploying' and reports_count > 1:
        status = 'pending'

    draft = get_draft(environment_id, session_id)

    if not 'services' in draft:
        return 'pending'

    def get_statuses(type):
        if type in draft['services']:
            services = draft['services'][type]
            return [get_service_status(environment_id,
                                       session_id,
                                       service) for service in services]
        else:
            return []

    is_inprogress = filter(lambda item: item == 'inprogress',
                           get_statuses('activeDirectories') +
                           get_statuses('webServers') +
                           get_statuses('aspNetApps'))

    if session_state == 'deploying' and is_inprogress > 1:
        status = 'inprogress'

    return status


def get_service_status(environment_id, session_id, service):
    status = 'draft'

    unit = get_session()
    session_state = unit.query(Session).get(session_id).state

    entities = [u['id'] for u in service['units']]
    reports_count = unit.query(Status).filter(
        Status.environment_id == environment_id
        and Status.session_id == session_id
        and Status.entity_id.in_(entities)
    ).count()

    if session_state == 'deployed':
        status = 'finished'

    if session_state == 'deploying' and reports_count == 0:
        status = 'pending'

    if session_state == 'deploying' and reports_count > 0:
        status = 'inprogress'

    return status
