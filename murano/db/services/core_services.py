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
import types

from oslo.utils import timeutils
from webob import exc

from murano.common import utils
from murano.db.services import environments as envs


class CoreServices(object):
    @staticmethod
    def get_service_status(environment_id, service_id):
        """Service can have one of three distinguished statuses:

         - Deploying: if environment has status deploying and there is at least
            one orchestration engine report for this service;
         - Pending: if environment has status `deploying` and there is no
            report from orchestration engine about this service;
         - Ready: If environment has status ready.

        :param environment_id: Service environment, we always know to which
            environment service belongs to
        :param service_id: Id of service for which we checking status.
        :return: Service status
        """
        # Now we assume that service has same status as environment.
        # TODO(ruhe): implement as designed and described above

        return envs.EnvironmentServices.get_status(environment_id)

    @staticmethod
    def get_data(environment_id, path, session_id=None):
        get_description = envs.EnvironmentServices.get_environment_description

        env_description = get_description(environment_id, session_id)

        if env_description is None:
            return None

        if 'services' not in env_description:
            return []

        result = utils.TraverseHelper.get(path, env_description)

        if path == '/services':
            get_status = CoreServices.get_service_status
            for srv in result:
                srv['?']['status'] = get_status(environment_id, srv['?']['id'])

        return result

    @staticmethod
    def post_data(environment_id, session_id, data, path):
        get_description = envs.EnvironmentServices.get_environment_description
        save_description = envs.EnvironmentServices.\
            save_environment_description

        env_description = get_description(environment_id, session_id)
        if env_description is None:
            raise exc.HTTPMethodNotAllowed
        if 'services' not in env_description:
            env_description['services'] = []

        if path == '/services':
            if isinstance(data, types.ListType):
                utils.TraverseHelper.extend(path, data, env_description)
            else:
                utils.TraverseHelper.insert(path, data, env_description)

        save_description(session_id, env_description)

        return data

    @staticmethod
    def put_data(environment_id, session_id, data, path):
        get_description = envs.EnvironmentServices.get_environment_description
        save_description = envs.EnvironmentServices.\
            save_environment_description

        env_description = get_description(environment_id, session_id)

        utils.TraverseHelper.update(path, data, env_description)
        env_description['?']['updated'] = str(timeutils.utcnow())

        save_description(session_id, env_description)

        return data

    @staticmethod
    def delete_data(environment_id, session_id, path):
        get_description = envs.EnvironmentServices.get_environment_description
        save_description = envs.EnvironmentServices.\
            save_environment_description

        env_description = get_description(environment_id, session_id)

        utils.TraverseHelper.remove(path, env_description)
        save_description(session_id, env_description)
