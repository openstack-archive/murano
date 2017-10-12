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

from oslo_db import exception as db_exc
from oslo_log import log as logging
import six
from webob import exc

from murano.api.v1 import request_statistics
from murano.common.i18n import _
from murano.common import policy
from murano.common import utils
from murano.common import wsgi
from murano.db import models
from murano.db.services import core_services
from murano.db.services import environment_templates as env_temps
from murano.db.services import environments as envs
from murano.db.services import sessions

LOG = logging.getLogger(__name__)

API_NAME = 'Templates'


class Controller(object):
    @request_statistics.stats_count(API_NAME, 'Index')
    def index(self, request):
        """Lists the env templates associated to an tenant-id

        It lists the env templates associated to an tenant-id.
        :param request: The operation request.
        :return: the env template description list.
        """
        LOG.debug('EnvTemplates:List')
        policy.check('list_env_templates', request.context)
        tenant_id = request.context.tenant
        filters = {}
        if request.GET.get('is_public'):
            is_public = request.GET.get('is_public', 'false').lower() == 'true'
            if not is_public:

                filters['is_public'] = False
                filters['tenant_id'] = tenant_id
            elif is_public:
                filters['is_public'] = True

            list_templates = env_temps.EnvTemplateServices.\
                get_env_templates_by(filters)

        else:
            filters = (models.EnvironmentTemplate.is_public,
                       models.EnvironmentTemplate.tenant_id == tenant_id)
            list_templates = env_temps.EnvTemplateServices.\
                get_env_templates_or_by(filters)

        list_templates = [temp.to_dict() for temp in list_templates]
        return {"templates": list_templates}

    @request_statistics.stats_count(API_NAME, 'Create')
    def create(self, request, body):
        """Creates the env template from the payload

        This payload can contain just the template name, or include
        also service information.
        :param request: the operation request.
        :param body: the env template description
        :return: the description of the created template.
        """
        LOG.debug('EnvTemplates:Create <Body {body}>'.format(body=body))
        policy.check('create_env_template', request.context)

        self._validate_body_name(body)
        try:
            LOG.debug('ENV TEMP NAME: {templ_name}>'.
                      format(templ_name=body['name']))
            template = env_temps.EnvTemplateServices.create(
                body.copy(), request.context.tenant)
            return template.to_dict()
        except db_exc.DBDuplicateEntry:
            msg = _('Env Template with specified name already exists')
            LOG.exception(msg)
            raise exc.HTTPConflict(msg)

    @request_statistics.stats_count(API_NAME, 'Show')
    def show(self, request, env_template_id):
        """It shows the description of a template

        :param request: the operation request.
        :param env_template_id: the env template ID.
        :return: the description of the env template.
        """
        LOG.debug('Templates:Show <Id: {templ_id}>'.format(
            templ_id=env_template_id))
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
        """It updates the description template

        :param request: the operation request.
        :param env_template_id: the env template ID.
        :param body: the description to be updated
        :return: the updated template description.
        """
        LOG.debug('Templates:Update <Id: {templ_id}, '
                  'Body: {body}>'.format(templ_id=env_template_id, body=body))
        target = {"env_template_id": env_template_id}
        policy.check('update_env_template', request.context, target)

        self._validate_request(request, env_template_id)
        try:
            LOG.debug('ENV TEMP NAME: {temp_name}>'.format(
                temp_name=body['name']))
            if not str(body['name']).strip():
                msg = _('Environment Template must contain at least one '
                        'non-white space symbol')
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
        """It deletes the env template

        :param request: the operation request.
        :param env_template_id: the template ID.
        """
        LOG.debug('EnvTemplates:Delete <Id: {templ_id}>'.format(
            templ_id=env_template_id))
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
        """Creates environment and session from template

        :param request: operation request
        :param env_template_id: environment template ID
        :param body: the environment name
        :return: session_id and environment_id
        """
        target = {"env_template_id": env_template_id}
        policy.check('create_environment', request.context, target)

        self._validate_request(request, env_template_id)
        LOG.debug('Templates:Create environment <Id: {templ_id}>'.
                  format(templ_id=env_template_id))
        template = env_temps.EnvTemplateServices.\
            get_env_template(env_template_id)
        self._validate_body_name(body)
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

    @request_statistics.stats_count(API_NAME, 'Clone')
    def clone(self, request, env_template_id, body):
        """Clones env template from another tenant

        It clones the env template from another env template
        from other tenant.
        :param request: the operation request.
        :param env_template_id: the env template ID.
        :param body: the request body.
        :return: the description of the created template.
        """

        LOG.debug('EnvTemplates:Clone <Env Template {1} for body {0}>'.
                  format(body, env_template_id))
        policy.check('clone_env_template', request.context)

        old_env_template = self._validate_exists(env_template_id)

        if not old_env_template.get('is_public'):
            msg = _('User has no access to these resources.')
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)
        self._validate_body_name(body)
        LOG.debug('ENV TEMP NAME: {0}'.format(body['name']))

        try:
            is_public = body.get('is_public', False)
            template = env_temps.EnvTemplateServices.clone(
                env_template_id, request.context.tenant, body['name'],
                is_public)
        except db_exc.DBDuplicateEntry:
            msg = _('Environment with specified name already exists')
            LOG.error(msg)
            raise exc.HTTPConflict(explanation=msg)

        return template.to_dict()

    def _validate_request(self, request, env_template_id):
        env_template = self._validate_exists(env_template_id)
        if env_template.is_public or request.context.is_admin:
            return
        if env_template.tenant_id != request.context.tenant:
            msg = _('User has no access to these resources.')
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

    def _validate_exists(self, env_template_id):
        env_template_exists = env_temps.EnvTemplateServices.env_template_exist
        if not env_template_exists(env_template_id):
            msg = _('EnvTemplate <TempId {temp_id}> is not found').format(
                temp_id=env_template_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)
        get_env_template = env_temps.EnvTemplateServices.get_env_template
        return get_env_template(env_template_id)

    def _validate_body_name(self, body):

        if not('name' in body and body['name'].strip()):
            msg = _('Please, specify a name of the environment template.')
            LOG.error(msg)
            raise exc.HTTPBadRequest(explanation=msg)

        name = six.text_type(body['name'])
        if len(name) > 255:
            msg = _('Environment template name should be 255 characters '
                    'maximum')
            LOG.error(msg)
            raise exc.HTTPBadRequest(explanation=msg)


def create_resource():
    return wsgi.Resource(Controller())
