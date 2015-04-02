#    Copyright (c) 2015, Telefonica I+D.
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

from oslo.db import exception as db_exc
from webob import exc

from murano.api.v1 import environments as envs_api
from murano.api.v1 import request_statistics
from murano.common.i18n import _
from murano.common import policy
from murano.common import utils
from murano.common import wsgi
from murano.db.services import core_services
from murano.db.services import environment_templates as env_temps
from murano.db.services import environments as envs
from murano.db.services import sessions
from murano.openstack.common import log as logging

LOG = logging.getLogger(__name__)

API_NAME = 'Templates'


class Controller(object):
    @request_statistics.stats_count(API_NAME, 'Index')
    def index(self, request):
        """It lists the env templates associated to an tenant-id.
        :param request: The operation request.
        :return: the env template description list.
        """
        LOG.debug('EnvTemplates:List')
        policy.check('list_env_templates', request.context)

        filters = {'tenant_id': request.context.tenant}
        list_templates = env_temps.EnvTemplateServices.\
            get_env_templates_by(filters)
        list_templates = [temp.to_dict() for temp in list_templates]

        return {"templates": list_templates}

    @request_statistics.stats_count(API_NAME, 'Create')
    def create(self, request, body):
        """It creates the env template from the payload obtaining.
        This payload can contain just the template name, or include
        also service information.
        :param request: the operation request.
        :param body: the env template description
        :return: the description of the created template.
        """
        LOG.debug('EnvTemplates:Create <Body {0}>'.format(body))
        policy.check('create_env_template', request.context)
        try:
            LOG.debug('ENV TEMP NAME: {0}>'.format(body['name']))
            if not envs_api.VALID_NAME_REGEX.match(str(body['name'])):
                msg = _('Environment Template must contain only alphanumeric '
                        'or "_-." characters, must start with alpha')
                LOG.exception(msg)
                raise exc.HTTPBadRequest(msg)
        except Exception:
                msg = _('Env template body is incorrect')
                LOG.exception(msg)
                raise exc.HTTPClientError(msg)
        try:
            template = env_temps.EnvTemplateServices.create(
                body.copy(), request.context.tenant)
            return template.to_dict()
        except db_exc.DBDuplicateEntry:
            msg = _('Env Template with specified name already exists')
            LOG.exception(msg)
            raise exc.HTTPConflict(msg)

    @request_statistics.stats_count(API_NAME, 'Show')
    def show(self, request, env_template_id):
        """It shows the description about a template.
        :param request: the operation request.
        :param env_template_id: the env template ID.
        :return: the description of the env template.
        """
        LOG.debug('Templates:Show <Id: {0}>'.format(env_template_id))
        target = {"env_template_id": env_template_id}
        policy.check('show_env_template', request.context, target)

        self._validate_request(request, env_template_id)

        template = env_temps.EnvTemplateServices.\
            get_env_template(env_template_id)
        temp = template.to_dict()

        get_data = core_services.CoreServices.get_template_data
        temp['services'] = get_data(env_template_id, '/services')
        return temp

    @request_statistics.stats_count(API_NAME, 'Update')
    def update(self, request, env_template_id, body):
        """It updates the description template.
        :param request: the operation request.
        :param env_template_id: the env template ID.
        :param body: the description to be updated
        :return: the updated template description.
        """
        LOG.debug('Templates:Update <Id: {0}, '
                  'Body: {1}>'.format(env_template_id, body))
        target = {"env_template_id": env_template_id}
        policy.check('update_env_template', request.context, target)

        self._validate_request(request, env_template_id)
        try:
            LOG.debug('ENV TEMP NAME: {0}>'.format(body['name']))
            if not envs_api.VALID_NAME_REGEX.match(str(body['name'])):
                msg = _('Env Template must contain only alphanumeric '
                        'or "_-." characters, must start with alpha')
                LOG.exception(msg)
                raise exc.HTTPBadRequest(msg)
        except Exception:
                msg = _('EnvTemplate body is incorrect')
                LOG.exception(msg)
                raise exc.HTTPBadRequest(msg)

        template = env_temps.EnvTemplateServices.update(env_template_id, body)
        return template.to_dict()

    @request_statistics.stats_count(API_NAME, 'Delete')
    def delete(self, request, env_template_id):
        """It deletes the env template.
        :param request: the operation request.
        :param env_template_id: the template ID.
        """
        LOG.debug('EnvTemplates:Delete <Id: {0}>'.format(env_template_id))
        target = {"env_template_id": env_template_id}
        policy.check('delete_env_template', request.context, target)
        self._validate_request(request, env_template_id)
        env_temps.EnvTemplateServices.delete(env_template_id)
        env_temps.EnvTemplateServices.remove(env_template_id)
        return

    def has_services(self, template):
        """"It checks if the template has services
        :param template: the template to check.
        :return: True or False
        """
        if not template.description:
            return False

        if (template.description.get('services')):
            return True
        return False

    @request_statistics.stats_count(API_NAME, 'Create_environment')
    def create_environment(self, request, env_template_id, body):
        """Creates environment and session from template.
        :param request: operation request
        :param env_template_id: environment template ID
        :param body: the environment name
        :return: session_id and environment_id
        """
        LOG.debug('Templates:Create environment <Id: {0}>'.
                  format(env_template_id))
        target = {"env_template_id": env_template_id}
        policy.check('create_environment', request.context, target)

        self._validate_request(request, env_template_id)
        template = env_temps.EnvTemplateServices.\
            get_env_template(env_template_id)

        if ('name' not in body or
                not envs_api.VALID_NAME_REGEX.match(str(body['name']))):
            msg = _('Environment must contain only alphanumeric '
                    'or "_-." characters, must start with alpha')
            LOG.error(msg)
            raise exc.HTTPBadRequest(explanation=msg)
        LOG.debug('ENVIRONMENT NAME: {0}>'.format(body['name']))

        try:
            environment = envs.EnvironmentServices.create(
                body.copy(), request.context)
        except db_exc.DBDuplicateEntry:
            msg = _('Environment with specified name already exists')
            LOG.exception(msg)
            raise exc.HTTPConflict(explanation=msg)

        user_id = request.context.user
        session = sessions.SessionServices.create(environment.id, user_id)

        if self.has_services(template):
            services_node = utils.TraverseHelper.get("services",
                                                     template.description)
            utils.TraverseHelper.update("/Objects/services",
                                        services_node,
                                        environment.description)

        envs.EnvironmentServices.save_environment_description(
            session.id,
            environment.description,
            inner=False
        )
        return {"session_id": session.id, "environment_id": environment.id}

    def _validate_request(self, request, env_template_id):
        env_template_exists = env_temps.EnvTemplateServices.env_template_exist
        if not env_template_exists(env_template_id):
            mng = _('EnvTemplate <TempId {0}> is not found').format(
                env_template_id)
            LOG.exception(mng)
            raise exc.HTTPNotFound(explanation=mng)
        get_env_template = env_temps.EnvTemplateServices.get_env_template
        env_template = get_env_template(env_template_id)
        if env_template.tenant_id != request.context.tenant:
            LOG.exception(_('User is not authorized to access '
                            'this tenant resources.'))
            raise exc.HTTPUnauthorized


def create_resource():
    return wsgi.Resource(Controller())
