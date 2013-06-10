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

import eventlet
from muranoapi.common import config
from muranoapi.db.services.environments import EnvironmentServices
from muranoapi.openstack.common import timeutils
from muranoapi.common import uuidutils


amqp = eventlet.patcher.import_patched('amqplib.client_0_8')
rabbitmq = config.CONF.rabbitmq


class SystemServices(object):
    @staticmethod
    def get_service_status(environment_id, service_id):
        """
        Service can have one of three distinguished statuses:

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
        # TODO: implement as designed and described above

        return EnvironmentServices.get_status(environment_id)

    @staticmethod
    def get_services(environment_id, service_type, session_id=None):
        """
        Get services of specified service_type from specified environment.
        If session_id is specified session state is checked, and if session is
        not deployed function returns service from the modified environment.

        :param environment_id: Environment Id
        :param service_type: Service service_type, e.g. activeDirectories
        :param session_id: Session Id
        :return: Service Object List
        """
        env_description = EnvironmentServices.get_environment_description(
            environment_id, session_id)

        if not 'services' in env_description:
            return []

        if service_type in env_description['services']:
            services = env_description['services'][service_type]
            for service in services:
                service['status'] = SystemServices.get_service_status(
                    environment_id, None)
            return services
        else:
            return []

    @staticmethod
    def get_service(environment_id, service_id, session_id=None):
        """
        Get services from specified environment. If session_id is specified
        session state is checked, and if session is not deployed function
        returns service from the modified environment.

        :param environment_id: Environment Id
        :param service_id: Service Id
        :param session_id: Session Id
        :return: Service Object
        :raise: ValueError if no services described in environment or if
            service not found
        """
        env_description = EnvironmentServices.get_environment_description(
            environment_id, session_id)

        if not 'services' in env_description:
            raise ValueError('This environment does not have services')

        services = []
        if 'activeDirectories' in env_description['services']:
            services = env_description['services']['activeDirectories']

        if 'webServers' in env_description['services']:
            services += env_description['services']['webServers']

        if 'aspNetApps' in env_description['services']:
            services += env_description['services']['aspNetApps']

        if 'webServerFarms' in env_description['services']:
            services += env_description['services']['webServerFarms']

        if 'aspNetAppFarms' in env_description['services']:
            services += env_description['services']['aspNetAppFarms']

        services = filter(lambda s: s.id == service_id, services)

        if len(services) > 0:
            return services[0]

        raise ValueError('Service with specified id does not exist')

    @staticmethod
    def create_active_directory(ad_params, session_id, environment_id):
        """
        Creates active directory service and saves it in specified session
        :param ad_params: Active Directory Params as Dict
        :param session_id: Session
        """
        env_description = EnvironmentServices.get_environment_description(
            environment_id, session_id)

        active_directory = ad_params
        active_directory['id'] = uuidutils.generate_uuid()
        active_directory['created'] = str(timeutils.utcnow())
        active_directory['updated'] = str(timeutils.utcnow())

        unit_count = 0
        for unit in active_directory['units']:
            unit_count += 1
            unit['id'] = uuidutils.generate_uuid()
            unit['name'] = 'dc{0}'.format(unit_count)

        if not 'services' in env_description:
            env_description['services'] = {}

        if not 'activeDirectories' in env_description['services']:
            env_description['services']['activeDirectories'] = []

        env_description['services']['activeDirectories'].append(
            active_directory)
        EnvironmentServices.save_environment_description(session_id,
                                                         env_description)

        return active_directory

    @staticmethod
    def create_web_server(ws_params, session_id, environment_id):
        """
        Creates web server service and saves it in specified session
        :param ws_params: Web Server Params as Dict
        :param session_id: Session
        """
        env_description = EnvironmentServices.get_environment_description(
            environment_id, session_id)

        web_server = ws_params
        web_server['id'] = uuidutils.generate_uuid()
        web_server['created'] = str(timeutils.utcnow())
        web_server['updated'] = str(timeutils.utcnow())

        unit_count = 0
        for unit in web_server['units']:
            unit_count += 1
            unit['id'] = uuidutils.generate_uuid()
            unit['name'] = web_server['name'] + '_instance_' + str(unit_count)

        if not 'services' in env_description:
            env_description['services'] = {}

        if not 'webServers' in env_description['services']:
            env_description['services']['webServers'] = []

        env_description['services']['webServers'].append(web_server)
        EnvironmentServices.save_environment_description(session_id,
                                                         env_description)

        return web_server

    @staticmethod
    def create_asp_application(params, session_id, environment_id):
        """
        Creates ASP.NET Application service and saves it in specified session
        :param params: Params as Dict
        :param session_id: Session
        """
        env_description = EnvironmentServices.get_environment_description(
            environment_id, session_id)

        aspApp = params
        aspApp['id'] = uuidutils.generate_uuid()
        aspApp['created'] = str(timeutils.utcnow())
        aspApp['updated'] = str(timeutils.utcnow())

        unit_count = 0
        for unit in aspApp['units']:
            unit_count += 1
            unit['id'] = uuidutils.generate_uuid()
            unit['name'] = aspApp['name'] + '_instance_' + str(unit_count)

        if not 'services' in env_description:
            env_description['services'] = {}

        if not 'aspNetApps' in env_description['services']:
            env_description['services']['aspNetApps'] = []

        env_description['services']['aspNetApps'].append(aspApp)
        EnvironmentServices.save_environment_description(session_id,
                                                         env_description)

        return aspApp

    @staticmethod
    def create_web_server_farm(ws_params, session_id, environment_id):
        """
        Creates web server farm service and saves it in specified session
        :param ws_params: Web Server Farm Params as Dict
        :param session_id: Session
        """
        env_description = EnvironmentServices.get_environment_description(
            environment_id, session_id)

        web_server_farm = ws_params
        web_server_farm['id'] = uuidutils.generate_uuid()
        web_server_farm['created'] = str(timeutils.utcnow())
        web_server_farm['updated'] = str(timeutils.utcnow())

        unit_count = 0
        for unit in web_server_farm['units']:
            unit_count += 1
            unit['id'] = uuidutils.generate_uuid()
            unit['name'] = web_server_farm['name'] + '_instance_' + \
                str(unit_count)

        if not 'services' in env_description:
            env_description['services'] = {}

        if not 'webServerFarms' in env_description['services']:
            env_description['services']['webServerFarms'] = []

        env_description['services']['webServerFarms'].append(web_server_farm)
        EnvironmentServices.save_environment_description(session_id,
                                                         env_description)

        return web_server_farm

    @staticmethod
    def create_asp_application_farm(params, session_id, environment_id):
        """
        Creates ASP.NET Application Farm service and saves it in
        specified session
        :param params: Params as Dict
        :param session_id: Session
        """
        env_description = EnvironmentServices.get_environment_description(
            environment_id, session_id)

        aspApp_farm = params
        aspApp_farm['id'] = uuidutils.generate_uuid()
        aspApp_farm['created'] = str(timeutils.utcnow())
        aspApp_farm['updated'] = str(timeutils.utcnow())

        unit_count = 0
        for unit in aspApp_farm['units']:
            unit_count += 1
            unit['id'] = uuidutils.generate_uuid()
            unit['name'] = aspApp_farm['name'] + '_instance_' + str(unit_count)

        if not 'services' in env_description:
            env_description['services'] = {}

        if not 'aspNetAppFarms' in env_description['services']:
            env_description['services']['aspNetAppFarms'] = []

        env_description['services']['aspNetAppFarms'].append(aspApp_farm)
        EnvironmentServices.save_environment_description(session_id,
                                                         env_description)

        return aspApp_farm

    @staticmethod
    def delete_service(service_id, service_type, session_id, environment_id):
        env_description = EnvironmentServices.get_environment_description(
            environment_id, session_id)

        if not 'services' in env_description:
            raise NameError('This environment does not have services')

        services = []
        if service_type in env_description['services']:
            services = env_description['services'][service_type]

        if service_id not in [srv['id'] for srv in services]:
            raise ValueError('Specified service does not exist')

        services = [srv for srv in services if srv['id'] != service_id]
        env_description['services'][service_type] = services

        EnvironmentServices.save_environment_description(session_id,
                                                         env_description)
