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

from murano.common.helpers import token_sanitizer
from murano.db import models
from murano.services import states


def get_environment(session, unit):
    environment = unit.query(models.Environment).get(
        session.environment_id)
    return environment


def update_task(action, session, task, unit):
    objects = session.description.get('Objects', None)
    session.state = states.SessionState.DELETING if objects is None \
        else states.SessionState.DEPLOYING
    task_info = models.Task()
    task_info.environment_id = session.environment_id
    if objects:
        task_info.description = token_sanitizer.TokenSanitizer().sanitize(
            dict(session.description.get('Objects')))
    task_info.action = task['action']
    status = models.Status()
    status.text = 'Action {0} is scheduled'.format(action)
    status.level = 'info'
    task_info.statuses.append(status)
    with unit.begin():
        unit.add(session)
        unit.add(task_info)
    return task_info.id
