# Copyright (c) 2015 Mirantis, Inc.
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

import os
import socket
import time
import uuid

from oslo_log import log as logging
import requests
import testresources
import testtools

import murano.tests.functional.common.utils as utils
import murano.tests.functional.engine.config as cfg


CONF = cfg.cfg.CONF

LOG = logging.getLogger(__name__)


class MuranoTestsCore(testtools.TestCase, testtools.testcase.WithAttributes,
                      testresources.ResourcedTestCase, utils.DeployTestMixin):
    """This manager provides access to Murano-api service."""
    @classmethod
    def setUpClass(cls):
        super(MuranoTestsCore, cls).setUpClass()

        cfg.load_config()
        cls._environments = []

    def setUp(self):
        super(MuranoTestsCore, self).setUp()

    def tearDown(self):
        super(MuranoTestsCore, self).tearDown()
        self.purge_environments()

# --------------------------Specific test methods------------------------------

    def wait_for_environment_deploy(self, environment):
        """Wait for successful deployment of Murano environment.

        Logging deployments and reports of failure.
        :param environment: Murano environment
        :return: Murano environment
        """
        start_time = time.time()
        status = environment.manager.get(environment.id).status
        while status != 'ready':
            status = environment.manager.get(environment.id).status
            if time.time() - start_time > 1800:
                time.sleep(60)
                self._log_report(environment)
                self.fail(
                    'Environment deployment is not finished in 1200 seconds')
            elif status == 'deploy failure':
                self._log_report(environment)
                time.sleep(60)
                self.fail('Environment has incorrect status {0}'.
                          format(status))
            time.sleep(5)
        LOG.debug('Environment {env_name} is ready'.format(
            env_name=environment.name))
        return environment.manager.get(environment.id)

    def status_check(self, environment, configurations, kubernetes=False):
        """Function which gives opportunity to check any count of instances.

        :param environment: Murano environment
        :param configurations: Array of configurations.
        :param kubernetes: Used for parsing multiple instances in one service
               False by default.
        Example: [[instance_name, *ports], [instance_name, *ports]] ...
        Example k8s: [[cluster['name'], instance_name, *ports], [...], ...]
        """
        for configuration in configurations:
            if kubernetes:
                service_name = configuration[0]
                LOG.debug('Service: {service_name}'.format(
                    service_name=service_name))
                inst_name = configuration[1]
                LOG.debug('Instance: {instance_name}'.format(
                    instance_name=inst_name))
                ports = configuration[2:]
                LOG.debug('Acquired ports: {ports}'.format(ports=ports))
                ip = self.get_k8s_ip_by_instance_name(environment, inst_name,
                                                      service_name)
                if ip and ports:
                    for port in ports:
                        self.check_port_access(ip, port)
                        self.check_k8s_deployment(ip, port)
                else:
                    self.fail('Instance does not have floating IP')
            else:
                inst_name = configuration[0]
                ports = configuration[1:]
                ip = self.get_ip_by_instance_name(environment, inst_name)
                if ip and ports:
                    for port in ports:
                        self.check_port_access(ip, port)
                else:
                    self.fail('Instance does not have floating IP')

    def deployment_success_check(self, environment, *ports):
        """Old style deployment check.

        Checks that environment deployment successfully. Only one instance in
        environment for this function is permitted for using this function.
        :param environment: Murano environment
        :param ports:
        """
        deployment = self.murano_client().deployments.list(environment.id)[-1]

        self.assertEqual('success', deployment.state,
                         'Deployment status is {0}'.format(deployment.state))

        ip = environment.services[0]['instance']['floatingIpAddress']

        if ip:
            for port in ports:
                self.check_port_access(ip, port)
        else:
            self.fail('Instance does not have floating IP')

    def check_port_access(self, ip, port):
        """Check that ports are opened on specific instances.

        :param ip: Instance's ip address
        :param port: Port that you want to check
        """
        result = 1
        start_time = time.time()
        while time.time() - start_time < 600:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex((str(ip), port))
            sock.close()
            if result == 0:
                break
            time.sleep(5)
        self.assertEqual(0, result, '%s port is closed on instance' % port)

    def check_k8s_deployment(self, ip, port):
        start_time = time.time()
        while time.time() - start_time < 600:
            try:
                LOG.debug('Checking: {ip}:{port}'.format(ip=ip, port=port))
                self.verify_connection(ip, port)
                return
            except RuntimeError as e:
                time.sleep(10)
                LOG.debug(e)
        self.fail('Containers are not ready')

    def check_path(self, env, path, inst_name=None):
        """Check path of deployed application using requests method 'GET'.

        :param env: Murano environment.
        :param path: Path to check
        Example: wordpress. e.g. function will check http://<ip>/wordpress
        :param inst_name: If defined, function will search through environment
        for instance ip and after check path.
        """
        environment = env.manager.get(env.id)
        if inst_name:
            ip = self.get_ip_by_instance_name(environment, inst_name)
        else:
            ip = environment.services[0]['instance']['floatingIpAddress']
        resp = requests.get('http://{0}/{1}'.format(ip, path))
        if resp.status_code == 200:
            return resp
        else:
            self.fail("Service path unavailable")

    def deploy_environment(self, environment, session):
        self.murano_client().sessions.deploy(environment.id, session.id)
        return self.wait_for_environment_deploy(environment)

    def _get_telnet_app(self):
        return {
            "instance": {
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "flavor": self.flavor,
                "image": self.linux,
                "name": "instance{0}".format(uuid.uuid4().hex[:5]),
            },
            "name": "app{0}".format(uuid.uuid4().hex[:5]),
            "?": {
                "type": "io.murano.apps.linux.Telnet",
                "id": str(uuid.uuid4())
            }
        }

    def get_test_app(self):
        return {
            "instance": {
                "flavor": self.flavor,
                "image": self.linux,
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": str(uuid.uuid4())
                },
                "name": self.rand_name('mrntest')
            },
            "name": self.rand_name('dummy'),
            "?": {
                "type": "io.murano.apps.test.UpdateExecutor",
                "id": str(uuid.uuid4())
            }
        }

    @classmethod
    def upload_app(cls, app_dir, name, tags):
        """Zip and upload application to Murano

        :param app_dir: Unzipped dir with an application
        :param name: Application name
        :param tags: Application tags
        :return: Uploaded package
        """
        zip_file_path = cls.zip_dir(os.path.dirname(__file__), app_dir)
        cls.init_list("_package_files")
        cls._package_files.append(zip_file_path)
        return cls.upload_package(
            name, tags, zip_file_path)
