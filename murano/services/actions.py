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

from murano.common import rpc
from murano.db import models
from murano.db.services import actions as actions_db
from murano.services import states


class ActionServices(object):
    @staticmethod
    def create_action_task(action_name, target_obj,
                           args, environment, session, context):
        action = None
        if action_name and target_obj:
            action = {
                'object_id': target_obj,
                'method': action_name,
                'args': args or {}
            }
        task = {
            'action': action,
            'model': session.description,
            'token': context.auth_token,
            'project_id': context.tenant,
            'user_id': context.user,
            'id': environment.id
        }
        if session.description['Objects'] is not None:
            task['model']['Objects']['?']['id'] = environment.id
            task['model']['Objects']['applications'] = \
                task['model']['Objects'].pop('services', [])

        return task

    @staticmethod
    def update_task(action, session, task, unit):
        session.state = states.SessionState.DEPLOYING
        task_info = models.Task()
        task_info.environment_id = session.environment_id
        task_info.description = dict(session.description.get('Objects'))
        task_info.action = task['action']
        status = models.Status()
        status.text = 'Action {0} is scheduled'.format(action[1]['name'])
        status.level = 'info'
        task_info.statuses.append(status)
        with unit.begin():
            unit.add(session)
            unit.add(task_info)

    @staticmethod
    def submit_task(action_name, target_obj,
                    args, environment, session, context, unit):
        task = ActionServices.create_action_task(
            action_name, target_obj, args,
            environment, session, context)
        task_id = actions_db.update_task(action_name, session, task, unit)
        rpc.engine().handle_task(task)
        return task_id

    @staticmethod
    def execute(action_id, session, unit, context, args=None):
        if args is None:
            args = {}
        environment = actions_db.get_environment(session, unit)
        action = ActionServices.find_action(session.description, action_id)
        if action is None:
            raise LookupError('Action is not found')
        if not action[1].get('enabled', True):
            raise ValueError('Cannot execute disabled action')

        return ActionServices.submit_task(
            action[1]['name'], action[0], args, environment,
            session, context, unit)

    @staticmethod
    def find_action(model, action_id):
        """Find_action for object def with specified action

        Traverses object model looking for an object definition
        containing specified action

        :param model: object model
        :param action_id: ID of an action
        :return: tuple (object id, {"name": "action_name_in_MuranoPL",
                                    "enabled": True })
        """
        if isinstance(model, list):
            for item in model:
                result = ActionServices.find_action(item, action_id)
                if result is not None:
                    return result
        elif isinstance(model, dict):
            if '?' in model and 'id' in model['?'] and \
                    '_actions' in model['?'] and \
                    action_id in model['?']['_actions']:
                return model['?']['id'], model['?']['_actions'][action_id]

            for obj in model.values():
                result = ActionServices.find_action(obj, action_id)
                if result is not None:
                    return result
        else:
            return None

    @staticmethod
    def get_result(environment_id, task_id, unit):
        task = unit.query(models.Task).filter_by(
            id=task_id, environment_id=environment_id).first()

        if task is not None:
            return task.result

        return None
