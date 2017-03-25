# Copyright (c) 2015 Telefonica I+D.
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

from murano.common.i18n import _
from murano.common import uuidutils
from murano.db import models
from murano.db import session as db_session

from oslo_db import exception as db_exc
from oslo_log import log as logging
from sqlalchemy.sql import or_

LOG = logging.getLogger(__name__)


class EnvTemplateServices(object):
    @staticmethod
    def get_env_templates_by(filters):
        """Returns list of environment-templates.

           :param filters: property filters
           :return: Returns list of environment-templates
        """

        unit = db_session.get_session()
        templates = unit.query(models.EnvironmentTemplate). \
            filter_by(**filters).all()

        return templates

    @staticmethod
    def get_env_templates_or_by(filters):
        """Returns list of environment-templates.

           :param filters: property filters
           :return: Returns list of environment-templates
        """
        unit = db_session.get_session()
        templates = unit.query(models.EnvironmentTemplate). \
            filter(or_(*filters)).all()

        return templates

    @staticmethod
    def create(env_template_params, tenant_id):
        """Creates environment-template with specified params, in particular - name.

           :param env_template_params: Dict, e.g. {'name': 'temp-name'}
           :param tenant_id: Tenant Id
           :return: Created Template
        """

        env_template_params['id'] = uuidutils.generate_uuid()
        env_template_params['tenant_id'] = tenant_id
        env_template = models.EnvironmentTemplate()
        env_template.update(env_template_params)

        unit = db_session.get_session()
        with unit.begin():
            try:
                unit.add(env_template)
            except db_exc.DBDuplicateEntry:
                msg = _('Environment template specified name already exists')
                LOG.error(msg)
                raise db_exc.DBDuplicateEntry(explanation=msg)
        env_template.update({'description': env_template_params})
        env_template.save(unit)

        return env_template

    @staticmethod
    def delete(env_template_id):
        """Deletes template.

           :param env_template_id: Template that is going to be deleted
        """

        env_temp_description = EnvTemplateServices.get_description(
            env_template_id)
        env_temp_description['description'] = None
        EnvTemplateServices.save_description(
            env_temp_description, env_template_id)

    @staticmethod
    def remove(env_template_id):
        """It deletes the environment template from database.

           :param env_template_id: Template Id to be deleted.
        """

        unit = db_session.get_session()
        template = unit.query(models.EnvironmentTemplate).get(env_template_id)
        if template:
            with unit.begin():
                unit.delete(template)

    @staticmethod
    def update(env_template_id, body):
        """It updates the description of an environment template.

           :param env_template_id: Template Id to be deleted.
           :param body: The description to be updated.
           :return: the template description updated
        """

        unit = db_session.get_session()
        template = unit.query(models.EnvironmentTemplate).get(env_template_id)
        template.update(body)
        template.save(unit)
        return template

    @staticmethod
    def get_description(env_template_id):
        """Returns environment template description for specified template.

           :param env_template_id: Template Id
           :return: environment-template Description Object
        """

        template = EnvTemplateServices.get_env_template(env_template_id)
        if template is None:
            raise ValueError("The environment template does not exist")
        return template.description

    @staticmethod
    def get_application_description(env_template_id):
        """Returns environment template description for specified applications.

           :param env_template_id: Template Id
           :return: Template Description Object
        """

        env_temp_desc = EnvTemplateServices.get_description(env_template_id)
        if "services" not in env_temp_desc:
            return []
        else:
            return env_temp_desc['services']

    @staticmethod
    def save_description(env_template_des, env_template_id=None):
        """Saves environment template description to specified session.

           :param env_template_des: Template Description
           :param env_template_id: The template ID.
        """
        unit = db_session.get_session()
        template = unit.query(models.EnvironmentTemplate).get(env_template_id)
        template.update({'description': env_template_des})
        template.save(unit)

    @staticmethod
    def env_template_exist(env_template_id):
        """It checks if the environment template exits in database.

           :param env_template_id: The template ID
        """

        template = EnvTemplateServices.get_env_template(env_template_id)
        if template is None:
            return False
        else:
            return True

    @staticmethod
    def get_env_template(env_template_id):
        """It obtains the environment template information from the database.

           :param env_template_id: The template ID
        """
        session = db_session.get_session()
        return session.query(models.EnvironmentTemplate).get(env_template_id)

    @staticmethod
    def clone(env_template_id, tenant_id, env_template_name, is_public):
        """Clones environment-template with specified params, in particular - name.

           :param env_template_params: Dict, e.g. {'name': 'temp-name'}
           :param tenant_id: Tenant Id
           :return: Created Template
        """

        template = EnvTemplateServices.get_env_template(env_template_id)
        env_template_params = template.to_dict()
        env_template_params['id'] = uuidutils.generate_uuid()
        env_template_params['tenant_id'] = tenant_id
        env_template_params['name'] = env_template_name
        env_template_params['is_public'] = is_public
        env_temp_desc = EnvTemplateServices.get_description(env_template_id)
        if "services" in env_temp_desc:
            env_template_params['services'] = env_temp_desc['services']

        env_template = models.EnvironmentTemplate()
        env_template.update(env_template_params)

        unit = db_session.get_session()
        with unit.begin():
            unit.add(env_template)
        env_template.update({'description': env_template_params})
        env_template.save(unit)
        return env_template
