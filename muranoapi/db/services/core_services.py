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

from muranoapi.common.utils import TraverseHelper, auto_id
from muranoapi.db.services.environments import EnvironmentServices
from muranoapi.openstack.common import timeutils


class CoreServices(object):
    @staticmethod
    def get_data(environment_id, path, session_id=None):
        get_description = EnvironmentServices.get_environment_description

        env_description = get_description(environment_id, session_id)

        if not 'services' in env_description:
            return []

        result = TraverseHelper.get(path, env_description)
        return result if result else []

    @staticmethod
    def post_data(environment_id, session_id, data, path):
        get_description = EnvironmentServices.get_environment_description
        save_description = EnvironmentServices.save_environment_description

        env_description = get_description(environment_id, session_id)
        if not 'services' in env_description:
            env_description['services'] = []

        data = auto_id(data)

        if path == '/services':
            data['created'] = str(timeutils.utcnow())
            data['updated'] = str(timeutils.utcnow())

            for idx, unit in enumerate(data['units']):
                unit['name'] = data['name'] + '_instance_' + str(idx)

        TraverseHelper.insert(path, data, env_description)
        save_description(session_id, env_description)

        return data

    @staticmethod
    def put_data(environment_id, session_id, data, path):
        get_description = EnvironmentServices.get_environment_description
        save_description = EnvironmentServices.save_environment_description

        env_description = get_description(environment_id, session_id)

        TraverseHelper.update(path, data, env_description)
        if path == '/services':
            data['updated'] = str(timeutils.utcnow())

        save_description(session_id, env_description)

        return data

    @staticmethod
    def delete_data(environment_id, session_id, path):
        get_description = EnvironmentServices.get_environment_description
        save_description = EnvironmentServices.save_environment_description

        env_description = get_description(environment_id, session_id)

        TraverseHelper.remove(path, env_description)
        save_description(session_id, env_description)
