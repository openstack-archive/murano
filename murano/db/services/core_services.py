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

from oslo_log import log as logging
from oslo_utils import timeutils
from webob import exc

from murano.common.i18n import _
from murano.common import utils
from murano.db.services import environment_templates as env_temp
from murano.db.services import environments as envs

LOG = logging.getLogger(__name__)


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
    def get_template_data(env_template_id, path):
        """It obtains the data for the template.

        It includes all the services. In case the path includes information
        such as the env_template_id, the information provided will
        be related to the entity specified in the path

        :param env_template_id: The env_template_id to obtain the data
        :param path: Id of service for which we checking status.
        :return: The template description
        """
        temp_description = env_temp.EnvTemplateServices.\
            get_description(env_template_id)

        if temp_description is None:
            return None

        if 'services' not in temp_description:
            return []

        result = utils.TraverseHelper.get(path, temp_description)
        if result is None:
            msg = _('Environment Template <EnvId {id}> is not found').format(
                id=env_template_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)
        return result

    @staticmethod
    def post_env_template_data(env_template_id, data, path):
        """It stores the template data inside the template description.

        :param env_template_id: The env_template_id to obtain the data
        :param data: the template description
        :param path: Id of service for which we checking status.
        :return: The template description
        """
        get_description = env_temp.EnvTemplateServices.get_description
        save_description = env_temp.EnvTemplateServices.save_description

        temp_description = get_description(env_template_id)
        if temp_description is None:
            msg = _('Environment Template <EnvId {id}> is not found').format(
                id=env_template_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)

        if 'services' not in temp_description:
            temp_description['services'] = []

        if path == '/services':
            if isinstance(data, list):
                utils.TraverseHelper.extend(path, data, temp_description)
            else:
                utils.TraverseHelper.insert(path, data, temp_description)
        save_description(temp_description)
        return data

    @staticmethod
    def post_application_data(env_template_id, data, path):
        """It stores the application data inside the template description.

        :param env_template_id: The env_template_id to obtain the data
        :param data: the template description
        :param path: Id of service for which we checking status.
        :return: The template description
        """
        get_description = env_temp.EnvTemplateServices.get_description
        save_description = env_temp.EnvTemplateServices.save_description

        temp_description = get_description(env_template_id)
        if temp_description is None:
            msg = _('Environment Template <EnvId {0}> is not found').format(
                env_template_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)

        if 'services' not in temp_description:
            temp_description['services'] = []

        if path == '/services':
            if isinstance(data, list):
                utils.TraverseHelper.extend(path, data, temp_description)
            else:
                utils.TraverseHelper.insert(path, data, temp_description)

        save_description(temp_description, env_template_id)

        return data

    @staticmethod
    def post_data(environment_id, session_id, data, path):
        get_description = envs.EnvironmentServices.get_environment_description
        save_description = envs.EnvironmentServices.\
            save_environment_description

        env_description = get_description(environment_id, session_id)
        if env_description is None:
            msg = _('Environment <EnvId {0}> is not found').format(
                environment_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)

        if 'services' not in env_description:
            env_description['services'] = []

        if path == '/services':
            if isinstance(data, list):
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

    @staticmethod
    def delete_env_template_data(env_template_id, path):
        """It deletes a template.

        :param env_template_id: The env_template_id to be deleted.
        :param path: The path to check.
        """
        get_description = env_temp.EnvTemplateServices.get_description
        save_description = env_temp.EnvTemplateServices.save_description

        tmp_description = get_description(env_template_id)
        if tmp_description is None:
            msg = _('Environment Template <EnvId {0}> is not found').format(
                env_template_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)

        utils.TraverseHelper.remove(path, tmp_description)
        save_description(tmp_description, env_template_id)
        return tmp_description

    @staticmethod
    def put_application_data(env_template_id, data, path):
        """It stores the application data inside the template description.

        :param env_template_id: The env_template_id to obtain the data
        :param data: the template description
        :param path: Id of service for which we checking status.
        :return: The template description
        """
        get_description = env_temp.EnvTemplateServices.get_description
        save_description = env_temp.EnvTemplateServices.save_description

        temp_description = get_description(env_template_id)
        if temp_description is None:
            msg = _('Environment Template <EnvId {0}> is not found').format(
                env_template_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)

        count = 0
        id = path[1:].split('/')[-1]
        for service in temp_description["services"]:
            if service["?"]["id"]:
                if service["?"]["id"] == id:
                    break
                count+1

        utils.TraverseHelper.update("services/{0}".format(count),
                                    data, temp_description)
        temp_description['updated'] = str(timeutils.utcnow())
        save_description(temp_description, env_template_id)
        return data
