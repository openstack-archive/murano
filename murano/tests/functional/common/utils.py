# Copyright (c) 2015 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import contextlib
import json
import os
import random
import re
import socket
import telnetlib
import time

from heatclient import client as heatclient
from keystoneclient import exceptions as ks_exceptions
import keystoneclient.v2_0 as keystoneclientv2
import keystoneclient.v3 as keystoneclientv3
from muranoclient import client as mclient
import muranoclient.common.exceptions as exceptions
from oslo_log import log as logging
import yaml

from murano.services import states
import murano.tests.functional.common.zip_utils_mixin as zip_utils
import murano.tests.functional.engine.config as cfg

CONF = cfg.cfg.CONF

LOG = logging.getLogger(__name__)


@contextlib.contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass


def memoize(f):
    """Saves result of decorated function to cache

    Decorator, which saves result of a decorated function
    to cache.
    TTL for cache is 1800 sec

    :param f: decorated function
    :return: saved result of a decorated function
    """
    cache = {}

    def decorated_function(*args):
        if args in cache:
            if time.time() - cache[args][1] < 1800:
                return cache[args][0]
            else:
                cache[args] = (f(*args), time.time())
                return cache[args][0]
        else:
            cache[args] = (f(*args), time.time())
            return cache[args][0]

    return decorated_function


class DeployTestMixin(zip_utils.ZipUtilsMixin):
    cfg.load_config()

# -----------------------------Clients methods---------------------------------
    @staticmethod
    @memoize
    def keystone_client():
        region = CONF.murano.region_name
        if re.match(".*/v3/?$", CONF.murano.auth_url):
            ksclient = keystoneclientv3
        else:
            ksclient = keystoneclientv2
        return ksclient.Client(username=CONF.murano.user,
                               password=CONF.murano.password,
                               tenant_name=CONF.murano.tenant,
                               auth_url=CONF.murano.auth_url,
                               region_name=region)

    @classmethod
    @memoize
    def heat_client(cls):
        heat_url = cls.keystone_client().service_catalog.url_for(
            service_type='orchestration', endpoint_type='publicURL')
        return heatclient.Client('1',
                                 endpoint=heat_url,
                                 token=cls.keystone_client().auth_token)

    @classmethod
    @memoize
    def murano_client(cls):
        murano_url = cls.get_murano_url()
        return mclient.Client('1',
                              endpoint=murano_url,
                              token=cls.keystone_client().auth_token)

# --------------------------Specific test methods------------------------------

    @classmethod
    def deploy_apps(cls, name, *apps):
        """Create and deploy environment.

        :param name: Murano environment name
        :param apps: App(s), described in JSON format
        :return: Murano environment
        """
        environment = cls.murano_client().environments.create({'name': name})
        cls.init_list("_environments")
        cls._environments.append(environment)
        session = cls.murano_client().sessions.configure(environment.id)
        for app in apps:
            cls.murano_client().services.post(
                environment.id,
                path='/',
                data=app,
                session_id=session.id)
        cls.murano_client().sessions.deploy(environment.id, session.id)
        return environment

    @classmethod
    def wait_for_final_status(cls, environment, timeout=300):
        """Function for wait final status of environment.

        :param environment: Murano environment.
        :param timeout: Timeout for waiting environment to get any status
               excluding DEPLOYING state
        """
        start_time = time.time()
        status = environment.manager.get(environment.id).status
        while states.SessionState.DEPLOYING == status:
            if time.time() - start_time > timeout:
                err_msg = ('Deployment not finished in {amount} seconds'
                           .format(amount=timeout))
                LOG.error(err_msg)
                raise RuntimeError(err_msg)
            time.sleep(5)
            status = environment.manager.get(environment.id).status
        dep = cls.murano_client().deployments.list(environment.id)
        reports = cls.murano_client().deployments.reports(environment.id,
                                                          dep[0].id)
        return status, ", ".join([r.text for r in reports])

# -----------------------------Reports methods---------------------------------

    @classmethod
    def get_last_deployment(cls, environment):
        """Gets last deployment of Murano environment.

        :param environment: Murano environment
        :return:
        """
        deployments = cls.murano_client().deployments.list(environment.id)
        return deployments[0]

    @classmethod
    def get_deployment_report(cls, environment, deployment):
        """Gets reports for environment with specific deployment.

        :param environment: Murano environment.
        :param deployment: Murano deployment for certain environment
        :return:
        """
        history = ''
        report = cls.murano_client().deployments.reports(
            environment.id, deployment.id)
        for status in report:
            history += '\t{0} - {1}\n'.format(status.created, status.text)
        return history

    @classmethod
    def _log_report(cls, environment):
        """Used for logging reports on failures.

        :param environment: Murano environment.
        """
        deployment = cls.get_last_deployment(environment)
        try:
            details = deployment.result['result']['details']
            LOG.warning('Details:\n {details}'.format(details=details))
        except Exception as e:
            LOG.error(e)
        report = cls.get_deployment_report(environment, deployment)
        LOG.debug('Report:\n {report}\n'.format(report=report))

# -----------------------------Service methods---------------------------------

    @classmethod
    def add_service(cls, environment, data, session, to_dict=False):
        """This function adds a specific service to environment.

        :param environment: Murano environment
        :param data: JSON with specific servive to add into
        :param session: Session that is open for environment
        :param to_dict: If True - returns a JSON object with service
                        If False - returns a specific class <Service>
        """

        LOG.debug('Added service:\n {data}'.format(data=data))
        service = cls.murano_client().services.post(environment.id,
                                                    path='/', data=data,
                                                    session_id=session.id)
        if to_dict:
            return cls._convert_service(service)
        else:
            return service

    @classmethod
    def services_list(cls, environment):
        """Get a list of environment services.

        :param environment: Murano environment
        :return: List of <Service> objects
        """
        return cls.murano_client().services.list(environment.id)

    @classmethod
    def get_service(cls, environment, service_name, to_dict=True):
        """Get a service with specific name from environment.

        :param to_dict: Convert service to JSON or not to convert
        :param environment: Murano environment
        :param service_name: Service name
        :return: JSON or <Service> object
        """
        for service in cls.services_list(environment):
            if service.name == service_name:
                return cls._convert_service(service) if to_dict else service

    @classmethod
    def _convert_service(cls, service):
        """Converts a <Service> to JSON object.

        :param service: <Service> object
        :return: JSON object
        """
        component = service.to_dict()
        component = json.dumps(component)
        return yaml.load(component)

    @classmethod
    def get_service_id(cls, service):
        """Gets id on <Service> object.

        :param service: <Service> object
        :return: ID of the Service
        """
        serv = cls._convert_service(service)
        serv_id = serv['?']['id']
        return serv_id

    @classmethod
    def delete_service(cls, environment, session, service):
        """This function removes a specific service from environment.

        :param environment: Murano environment
        :param session: Session fir urano environment
        :param service: <Service> object
        :return: Updated murano environment
        """
        cls.murano_client().services.delete(
            environment.id, path='/{0}'.format(cls.get_service_id(service)),
            session_id=session.id)
        LOG.debug('Service with name {0} from environment {1} successfully '
                  'removed'.format(environment.name, service.name))
        updated_env = cls.get_environment(environment)
        return updated_env


# -----------------------------Packages methods--------------------------------

    @classmethod
    def upload_package(cls, package_name, body, app):
        """Uploads a .zip package with parameters to Murano.

        :param package_name: Package name in Murano repository
        :param body: Categories, tags, etc.
                     e.g. {
                           "categories": ["Application Servers"],
                           "tags": ["tag"]
                           }
        :param app: Correct .zip archive with the application
        :return: Package
        """
        files = {'{0}'.format(package_name): open(app, 'rb')}
        package = cls.murano_client().packages.create(body, files)
        cls.init_list("_packages")
        cls._packages.append(package)
        return package

# ------------------------------Common methods---------------------------------

    @classmethod
    def rand_name(cls, name='murano'):
        """Generates random string.

        :param name: Basic name
        :return:
        """
        return name + str(random.randint(1, 0x7fffffff))

    @classmethod
    def init_list(cls, list_name):
        if not hasattr(cls, list_name):
            setattr(cls, list_name, [])

    @classmethod
    def get_murano_url(cls):
        try:
            url = cls.keystone_client().service_catalog.url_for(
                service_type='application-catalog', endpoint_type='publicURL')
        except ks_exceptions.EndpointNotFound:
            url = CONF.murano.murano_url
            LOG.warning("Murano endpoint not found in Keystone. Using CONF.")
        return url if 'v1' not in url else "/".join(
            url.split('/')[:url.split('/').index('v1')])

    @classmethod
    def verify_connection(cls, ip, port):
        """Try to connect to specific ip:port with telnet.

        :param ip: Ip that you want to check
        :param port: Port that you want to check
        :return: :raise RuntimeError:
        """
        tn = telnetlib.Telnet(ip, port)
        tn.write('GET / HTTP/1.0\n\n')
        try:
            buf = tn.read_all()
            LOG.debug('Data:\n {data}'.format(data=buf))
            if len(buf) != 0:
                tn.sock.sendall(telnetlib.IAC + telnetlib.NOP)
                return
            else:
                raise RuntimeError('Resource at {0}:{1} not exist'.
                                   format(ip, port))
        except socket.error as e:
            LOG.error('Socket Error: {error}'.format(error=e))

    @classmethod
    def get_ip_by_appname(cls, environment, appname):
        """Returns ip of instance with a deployed application using app name.

        :param environment: Murano environment
        :param appname: Application name or substring of application name
        :return:
        """
        for service in environment.services:
            if appname in service['name']:
                return service['instance']['floatingIpAddress']

    @classmethod
    def get_ip_by_instance_name(cls, environment, inst_name):
        """Returns ip of instance using instance name.

        :param environment: Murano environment
        :param name: String, which is substring of name of instance or name of
        instance
        :return:
        """
        for service in environment.services:
            if inst_name in service['instance']['name']:
                return service['instance']['floatingIpAddress']

    @classmethod
    def get_k8s_ip_by_instance_name(cls, environment, inst_name, service_name):
        """Returns ip of specific kubernetes node (gateway, master, minion).

        Search depends on service name of kubernetes and names of spawned
        instances
        :param environment: Murano environment
        :param inst_name: Name of instance or substring of instance name
        :param service_name: Name of Kube Cluster application in Murano
        environment
        :return: Ip of Kubernetes instances
        """
        for service in environment.services:
            if service_name in service['name']:
                if "gateway" in inst_name:
                    for gateway in service['gatewayNodes']:
                        if inst_name in gateway['instance']['name']:
                            LOG.debug(gateway['instance']['floatingIpAddress'])
                            return gateway['instance']['floatingIpAddress']
                elif "master" in inst_name:
                    LOG.debug(service['masterNode']['instance'][
                        'floatingIpAddress'])
                    return service['masterNode']['instance'][
                        'floatingIpAddress']
                elif "minion" in inst_name:
                    for minion in service['minionNodes']:
                        if inst_name in minion['instance']['name']:
                            LOG.debug(minion['instance']['floatingIpAddress'])
                            return minion['instance']['floatingIpAddress']

# -----------------------------Cleanup methods---------------------------------

    @classmethod
    def purge_uploaded_packages(cls):
        """Cleanup for uploaded packages."""
        cls.init_list("_packages")
        try:
            for pkg in cls._packages:
                with ignored(Exception):
                    cls.murano_client().packages.delete(pkg.id)
        finally:
            cls._packages = []
        cls.init_list("_package_files")
        try:
            for pkg_file in cls._package_files:
                os.remove(pkg_file)
        finally:
            cls._package_files = []

    @classmethod
    def purge_environments(cls):
        """Cleanup for created environments."""
        cls.init_list("_environments")
        try:
            for env in cls._environments:
                with ignored(Exception):
                    LOG.debug('Processing cleanup for environment {0} ({1})'.
                              format(env.name, env.id))
                    cls.environment_delete(env.id)
                    cls.purge_stacks(env.id)
                    time.sleep(5)
        finally:
            cls._environments = []

    @classmethod
    def purge_stacks(cls, environment_id):
        stack = cls._get_stack(environment_id)
        if not stack:
            return
        else:
            cls.heat_client().stacks.delete(stack.id)

# -----------------------Methods for environment CRUD--------------------------

    @classmethod
    def create_environment(cls, name=None):
        """Creates Murano environment with random name.


        :param name: Environment name
        :return: Murano environment
        """
        if not name:
            name = cls.rand_name('MuranoTe')
        environment = cls.murano_client().environments.create({'name': name})
        cls._environments.append(environment)
        return environment

    @classmethod
    def get_environment(cls, environment):
        """Refresh <Environment> variable.

        :param environment: Murano environment.
        :return: Murano environment.
        """
        return cls.murano_client().environments.get(environment.id)

    @classmethod
    def environment_delete(cls, environment_id, timeout=180):
        """Remove Murano environment.

        :param environment_id: ID of Murano environment
        :param timeout: Timeout to environment get deleted
        :return: :raise RuntimeError:
        """
        try:
            cls.murano_client().environments.delete(environment_id)

            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    cls.murano_client().environments.get(environment_id)
                except exceptions.HTTPNotFound:
                    LOG.debug('Environment with id {0} successfully deleted.'.
                              format(environment_id))
                    return
            err_msg = ('Environment {0} was not deleted in {1} seconds'.
                       format(environment_id, timeout))
            LOG.error(err_msg)
            raise RuntimeError(err_msg)
        except Exception as exc:
            LOG.debug('Environment with id {0} going to be abandoned.'.
                      format(environment_id))
            LOG.exception(exc)
            cls.murano_client().environments.delete(environment_id,
                                                    abandon=True)

# -----------------------Methods for session actions---------------------------

    @classmethod
    def create_session(cls, environment):
        return cls.murano_client().sessions.configure(environment.id)

    @classmethod
    def delete_session(cls, environment, session):
        return cls.murano_client().sessions.delete(environment.id, session.id)


# -------------------------------Heat methods----------------------------------

    @classmethod
    def _get_stack(cls, environment_id):

        for stack in cls.heat_client().stacks.list():
            if environment_id in stack.description:
                return stack

    @classmethod
    def get_stack_template(cls, stack):
        return cls.heat_client().stacks.template(stack.stack_name)
