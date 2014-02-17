# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Mirantis, Inc.
# All Rights Reserved.
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

import json
import socket
import requests
import os
import novaclient.v1_1.client as nvclient
import tempest.test
import tempest.api.murano.config as cfg
from tempest import clients
from tempest.common import rest_client


class MuranoTest(tempest.test.BaseTestCase):

    @classmethod
    def setUpClass(cls):
        """
            This method allows to initialize authentication before
            each test case and define parameters of Murano API Service
            This method also create environment for all tests
        """

        super(MuranoTest, cls).setUpClass()

        if not cfg.murano.service_available:
            raise cls.skipException("Murano tests are disabled")
        user = cls.config.identity.admin_username
        password = cls.config.identity.admin_password
        tenant = cls.config.identity.admin_tenant_name
        auth_url = cls.config.identity.uri
        client_args = (cls.config, user, password, auth_url, tenant)

        cls.client = rest_client.RestClient(*client_args)
        cls.client.service = 'identity'
        cls.token = cls.client.get_auth()
        cls.client.base_url = cfg.murano.murano_url
        cls.environments = []
        cls.inst_wth_fl_ip = []

        cls.linux = 'linux'
        cls.windows = 'windows'
        cls.demo = 'demo'

    def tearDown(self):
        """
            This method allows to clean up after each test.
            The main task for this method - delete environment after
            PASSED and FAILED tests.
        """

        super(MuranoTest, self).tearDown()

        for environment in self.environments:
            try:
                self.delete_environment(environment['id'])
            except Exception:
                pass
        for inst in self.inst_wth_fl_ip:
            try:
                self.remove_floating_ip(inst)
            except Exception:
                pass

    def create_environment(self, name):
        """
            This method allows to create environment.

            Input parameters:
              name - Name of new environment

            Returns response and new environment.
        """

        post_body = '{"name": "%s"}' % name
        resp, body = self.client.post('environments', post_body,
                                      self.client.headers)

        return resp, json.loads(body)

    def delete_environment(self, environment_id):
        """
            This method allows to delete environment

            Input parameters:
              environment_id - ID of deleting environment
        """
        self.client.delete('environments/' + str(environment_id),
                           self.client.headers)

    def update_environment(self, environment_id, environment_name):
        """
            This method allows to update environment instance

            Input parameters:
              environment_id - ID of updating environment
              environment_name - name of updating environment
        """
        post_body = '{"name": "%s"}' % (environment_name + "-changed")
        resp, body = self.client.put('environments/' + str(environment_id),
                                     post_body, self.client.headers)
        return resp, json.loads(body)

    def get_list_environments(self):
        """
            This method allows to get a list of existing environments

            Returns response and list of environments
        """
        resp, body = self.client.get('environments',
                                     self.client.headers)
        return resp, json.loads(body)

    def get_environment_by_id(self, environment_id):
        """
            This method allows to get environment's info by id

            Input parameters:
              environment_id - ID of needed environment
            Returns response and environment's info
        """
        resp, body = self.client.get('environments/' + str(environment_id),
                                     self.client.headers)
        return resp, json.loads(body)

    def nova_auth(self):
        user = self.config.identity.admin_username
        password = self.config.identity.admin_password
        tenant = self.config.identity.admin_tenant_name
        auth_url = self.config.identity.uri
        nova = nvclient.Client(user, password, tenant, auth_url,
                               service_type="compute")
        return nova

    def search_instances(self, environment_id, hostname):
        nova = self.nova_auth()
        somelist = []
        for i in nova.servers.list():
            if ((str(environment_id) in str(
                    i.name)) and (str(hostname) in str(i.name))):
                somelist.append(i.id)
        return somelist

    def add_floating_ip(self, instance_id):
        nova = self.nova_auth()
        pool = nova.floating_ip_pools.list()[0].name
        ip = nova.floating_ips.create(pool)
        nova.servers.get(instance_id).add_floating_ip(ip)
        return ip.ip

    def remove_floating_ip(self, instance_id):
        nova = self.nova_auth()
        fl_ips = nova.floating_ips.findall(instance_id=instance_id)
        for fl_ip in fl_ips:
            nova.floating_ips.delete(fl_ip.id)
        return None

    def socket_check(self, ip, port):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((str(ip), port))
        sock.close()
        return result

    def create_session(self, environment_id):
        """
            This method allow to create session

            Input parameters:
              environment_id - ID of environment
                   where session should be created
        """
        post_body = None
        resp, body = self.client.post('environments/' + str(environment_id) +
                                      '/configure',
                                      post_body, self.client.headers)
        return resp, json.loads(body)

    def get_session_info(self, environment_id, session_id):
        """
            This method allow to get session's info

            Input parameters:
              environment_id - ID of environment
                             where needed session was created
              session_id - ID of needed session
            Return response and session's info
        """
        resp, body = self.client.get('environments/' + str(environment_id) +
                                     '/sessions/' + str(session_id),
                                     self.client.headers)
        return resp, json.loads(body)

    def delete_session(self, environment_id, session_id):
        """
            This method allow to delete session

            Input parameters:
              environment_id - ID of environment
                             where needed session was created
              session_id - ID of needed session
        """
        self.client.delete('environments/' + str(environment_id) +
                           '/sessions/' + str(session_id), self.client.headers)

    def create_AD(self, environment_id, session_id):
        """
            This method allow to add AD

            Input parameters:
              environment_id - ID of current environment
              session_id - ID of current session
        """
        post_body = {"type": "activeDirectory", "name": "ad.local",
                     "adminPassword": "P@ssw0rd", "domain": "ad.local",
                     "availabilityZone": "nova",
                     "unitNamingPattern": "adinstance",
                     "flavor": "m1.medium", "osImage":
                     {"type": "ws-2012-std", "name": self.windows, "title":
                         "Windows Server 2012 Standard"},
                     "configuration": "standalone",
                     "units": [{"isMaster": True,
                                "recoveryPassword": "P@ssw0rd",
                                "location": "west-dc"}]}

        post_body = json.dumps(post_body)
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.post('environments/' + str(environment_id) +
                                      '/services', post_body,
                                      self.client.headers)
        return resp, json.loads(body)

    def create_IIS(self, environment_id, session_id, domain_name=""):
        """
            This method allow to add IIS

            Input parameters:
              environment_id - ID of current environment
              session_id - ID of current session
        """
        iis_name = "IISSERVICE"
        creds = {'username': 'Administrator',
                 'password': 'P@ssw0rd'}
        post_body = {"type": "webServer", "domain": domain_name,
                     "availabilityZone": "nova", "name": iis_name,
                     "adminPassword": "P@ssw0rd",
                     "unitNamingPattern": "iisinstance",
                     "osImage": {"type": "ws-2012-std", "name": self.windows,
                                 "title": "Windows Server 2012 Standard"},
                     "units": [{}], "credentials": creds,
                     "flavor": "m1.medium"}
        post_body = json.dumps(post_body)
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.post('environments/' + str(environment_id) +
                                      '/services', post_body,
                                      self.client.headers)
        return resp, json.loads(body)

    def create_apsnet(self, environment_id, session_id, domain_name=""):
        """
            This method allow to add apsnet

            Input parameters:
              environment_id - ID of current environment
              session_id - ID of current session
        """
        creds = {'username': 'Administrator',
                 'password': 'P@ssw0rd'}
        post_body = {"type": "aspNetApp", "domain": domain_name,
                     "availabilityZone": "nova",
                     "name": "someasp", "repository":
                     "git://github.com/Mirantis/murano-mvc-demo.git",
                     "adminPassword": "P@ssw0rd",
                     "unitNamingPattern": "aspnetinstance",
                     "osImage": {"type": "ws-2012-std", "name": self.windows,
                                 "title": "Windows Server 2012 Standard"},
                     "units": [{}], "credentials": creds,
                     "flavor": "m1.medium"}
        post_body = json.dumps(post_body)
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.post('environments/' + str(environment_id) +
                                      '/services', post_body,
                                      self.client.headers)
        return resp, json.loads(body)

    def create_IIS_farm(self, environment_id, session_id, domain_name=""):
        """
            This method allow to add IIS farm

            Input parameters:
              environment_id - ID of current environment
              session_id - ID of current session
        """
        creds = {'username': 'Administrator', 'password': 'P@ssw0rd'}
        post_body = {"type": "webServerFarm", "domain": domain_name,
                     "availabilityZone": "nova", "name": "someIISFARM",
                     "adminPassword": "P@ssw0rd", "loadBalancerPort": 80,
                     "unitNamingPattern": "",
                     "osImage": {"type": "ws-2012-std", "name": self.windows,
                                 "title": "Windows Server 2012 Standard"},
                     "units": [{}, {}],
                     "credentials": creds, "flavor": "m1.medium"}
        post_body = json.dumps(post_body)
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.post('environments/' + str(environment_id) +
                                      '/services', post_body,
                                      self.client.headers)
        return resp, json.loads(body)

    def create_apsnet_farm(self, environment_id, session_id, domain_name=""):
        """
            This method allow to add apsnet farm

            Input parameters:
              environment_id - ID of current environment
              session_id - ID of current session
        """
        creds = {'username': 'Administrator', 'password': 'P@ssw0rd'}
        post_body = {"type": "aspNetAppFarm", "domain": domain_name,
                     "availabilityZone": "nova", "name": "SomeApsFarm",
                     "repository":
                             "git://github.com/Mirantis/murano-mvc-demo.git",
                     "adminPassword": "P@ssw0rd", "loadBalancerPort": 80,
                     "unitNamingPattern": "",
                     "osImage": {"type": "ws-2012-std", "name": self.windows,
                                 "title": "Windows Server 2012 Standard"},
                     "units": [{}, {}],
                     "credentials": creds, "flavor": "m1.medium"}
        post_body = json.dumps(post_body)
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.post('environments/' + str(environment_id) +
                                      '/services', post_body,
                                      self.client.headers)
        return resp, json.loads(body)

    def create_SQL(self, environment_id, session_id, domain_name=""):
        """
            This method allow to add SQL

            Input parameters:
              environment_id - ID of current environment
              session_id - ID of current session
        """
        post_body = {"type": "msSqlServer", "domain": domain_name,
                     "availabilityZone": "nova", "name": "SQLSERVER",
                     "adminPassword": "P@ssw0rd",
                     "unitNamingPattern": "sqlinstance",
                     "saPassword": "P@ssw0rd", "mixedModeAuth": True,
                     "osImage": {"type": "ws-2012-std", "name": self.windows,
                                 "title": "Windows Server 2012 Standard"},
                     "units": [{}],
                     "credentials": {"username": "Administrator",
                                     "password": "P@ssw0rd"},
                     "flavor": "m1.medium"}
        post_body = json.dumps(post_body)
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.post('environments/' + str(environment_id) +
                                      '/services', post_body,
                                      self.client.headers)
        return resp, json.loads(body)

    def create_SQL_cluster(self, environment_id, session_id, domain_name=""):
        """
            This method allow to add SQL cluster

            Input parameters:
              environment_id - ID of current environment
              session_id - ID of current session
        """
        AG = cfg.murano.agListnerIP
        clIP = cfg.murano.clusterIP
        post_body = {"domain": domain_name, "domainAdminPassword": "P@ssw0rd",
                     "externalAD": False,
                     "sqlServiceUserName": "Administrator",
                     "sqlServicePassword": "P@ssw0rd",
                     "osImage": {"type": "ws-2012-std", "name": self.windows,
                                 "title": "Windows Server 2012 Standard"},
                     "agListenerName": "SomeSQL_AGListner",
                     "flavor": "m1.medium",
                     "agGroupName": "SomeSQL_AG",
                     "domainAdminUserName": "Administrator",
                     "agListenerIP": AG,
                     "clusterIP": clIP,
                     "type": "msSqlClusterServer", "availabilityZone": "nova",
                     "adminPassword": "P@ssw0rd",
                     "clusterName": "SomeSQL", "mixedModeAuth": True,
                     "unitNamingPattern": "",
                     "units": [{"isMaster": True, "name": "node1",
                                "isSync": True},
                               {"isMaster": False, "name": "node2",
                                "isSync": True}],
                     "name": "Sqlname", "saPassword": "P@ssw0rd",
                     "databases": ['NewDB']}
        post_body = json.dumps(post_body)
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.post('environments/' + str(environment_id) +
                                      '/services', post_body,
                                      self.client.headers)
        return resp, json.loads(body)

    def create_linux_telnet(self, environment_id, session_id):
        post_body = {"availabilityZone": "nova", "name": "LinuxTelnet",
                     "deployTelnet": True, "unitNamingPattern": "telnet",
                     "keyPair": "murano-lb-key",
                     "osImage": {"type": "linux", "name": self.linux,
                                 "title": "Linux Image"},
                     "units": [{}],
                     "flavor": "m1.small", "type": "linuxTelnetService"}
        post_body = json.dumps(post_body)
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.post('environments/' + str(environment_id) +
                                      '/services', post_body,
                                      self.client.headers)
        return resp, json.loads(body)

    def create_linux_apache(self, environment_id, session_id):
        post_body = {"availabilityZone": "nova", "name": "LinuxApache",
                     "deployApachePHP": True, "unitNamingPattern": "apache",
                     "keyPair": "murano-lb-key",
                     "instanceCount": [{}],
                     "osImage": {"type": "linux", "name": self.linux,
                                 "title": "Linux Image"},
                     "units": [{}],
                     "flavor": "m1.small", "type": "linuxApacheService"}
        post_body = json.dumps(post_body)
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.post('environments/' + str(environment_id) +
                                      '/services', post_body,
                                      self.client.headers)
        return resp, json.loads(body)

    def create_demo_service(self, environment_id, session_id):
        post_body = {"availabilityZone": "nova", "name": "demo",
                     "unitNamingPattern": "host",
                     "osImage": {"type": "cirros.demo", "name": self.demo,
                                 "title": "Demo"},
                     "units": [{}], "flavor": "m1.small",
                     "configuration": "standalone", "type": "demoService"}
        post_body = json.dumps(post_body)
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.post('environments/' + str(environment_id) +
                                      '/services', post_body,
                                      self.client.headers)
        return resp, json.loads(body)

    def delete_service(self, environment_id, session_id, service_id):
        """
            This method allow to delete service

            Input parameters:
              environment_id - ID of current environment
              session_id - ID of current session
              service_id - ID of needed service
        """
        self.client.headers.update({'X-Configuration-Session': session_id})
        self.client.delete('environments/' + str(environment_id)
                           + '/services/' + str(service_id),
                           self.client.headers)

    def get_list_services(self, environment_id, session_id):
        """
            This method allow to get list of services

            Input parameters:
              environment_id - ID of current environment
              session_id - ID of current session
        """
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.get('environments/' + str(environment_id) +
                                     '/services',
                                     self.client.headers)
        return resp, json.loads(body)

    def get_service_info(self, environment_id, session_id, service_id):
        """
            This method allow to get detailed service info

            Input parameters:
              environment_id - ID of current environment
              session_id - ID of current session
              service_id - ID of needed service
        """
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.get('environments/' + str(environment_id) +
                                     '/services/' + str(service_id),
                                     self.client.headers)
        return resp, json.loads(body)

    def update_service(self, environment_id, session_id, service_id, s_body):
        """
            This method allows to update service

            Input parameters:
              environment_id - env's id
              session_id - session_id where service is attach
              service_id - service id of updating service
              s_body - json obj
        """
        s_body['flavor'] = "m1.small"
        post_body = json.dumps(s_body)
        self.client.headers.update({'X-Configuration-Session': session_id})
        resp, body = self.client.put('environments/' + str(environment_id) +
                                     '/services/' + str(service_id),
                                     post_body, self.client.headers)
        return resp, json.loads(body)

    def deploy_session(self, environment_id, session_id):
        """
            This method allow to send environment on deploy

            Input parameters:
              environment_id - ID of current environment
              session_id - ID of current session
        """
        post_body = None
        resp = self.client.post('environments/' + str(environment_id) +
                                '/sessions/' + str(session_id) +
                                '/deploy', post_body, self.client.headers)
        return resp

    def get_deployments_list(self, environment_id):
        """
            This method allow to get list of deployments

            Input parameters:
              environment_id - ID of current environment
        """
        resp, body = self.client.get('environments/' + str(environment_id) +
                                     '/deployments', self.client.headers)
        return resp, json.loads(body)

    def get_deployment_info(self, environment_id, deployment_id):
        """
            This method allow to get detailed info about deployment

            Input parameters:
              environment_id - ID of current environment
              deployment_id - ID of needed deployment
        """
        resp, body = self.client.get('environments/' + str(environment_id) +
                                     '/deployments/' + str(deployment_id),
                                     self.client.headers)
        return resp, json.loads(body)


class MuranoMeta(tempest.test.BaseTestCase):

    @classmethod
    def setUpClass(cls):

        super(MuranoMeta, cls).setUpClass()
        if not cfg.murano.service_available:
            raise cls.skipException("Murano tests is disabled")
        user = cls.config.identity.admin_username
        password = cls.config.identity.admin_password
        tenant = cls.config.identity.admin_tenant_name
        auth_url = cls.config.identity.uri
        client_args = (cls.config, user, password, auth_url, tenant)
        cls.client = rest_client.RestClient(*client_args)
        cls.client.service = 'identity'
        cls.token = cls.client.get_auth()
        cls.client.base_url = cfg.murano.metadata_url
        cls.objs = []
        cls.services = []

    def tearDown(self):
        super(MuranoMeta, self).tearDown()

        for obj in self.objs:
            try:
                self.delete_metadata_obj_or_folder(obj)
            except Exception:
                pass

        for service in self.services:
            try:
                self.delete_service(service)
            except Exception:
                pass

    def get_ui_definitions(self):
        resp, body = self.client.get('v1/client/ui', self.client.headers)
        return resp, body

    def get_conductor_metadata(self):
        resp, body = self.client.get('v1/client/conductor',
                                     self.client.headers)
        return resp, body

    def get_list_metadata_objects(self, path):
        resp, body = self.client.get('v1/admin/' + path, self.client.headers)
        return resp, body

    def get_metadata_object(self, object):
        resp, body = self.client.get('v1/admin/' + object, self.client.headers)
        return resp, body

    def upload_metadata_object(self, path, filename='testfile.txt'):
        with open(filename, 'w') as f:
            f.write("It's a test file")
        files = {'file': open(filename, 'rb')}
        headers = {'X-Auth-Token': self.token}
        resp = requests.post('%s/v1/admin/%s' % (self.client.base_url, path),
                             files=files, headers=headers)
        os.remove(filename)
        return resp

    def create_directory(self, path, name):
        post_body = None
        resp, body = self.client.put('v1/admin/' + path + name, post_body,
                                     self.client.headers)
        return resp, json.loads(body)

    def delete_metadata_obj_or_folder(self, object):
        resp, body = self.client.delete('v1/admin/' + object,
                                        self.client.headers)
        return resp, json.loads(body)

    def create_new_service(self, name):
        post_body = {"name": name, "version": "0.1",
                     "full_service_name": name,
                     "service_display_name": name}
        post_body = json.dumps(post_body)
        resp, body = self.client.put('v1/admin/services/' + name, post_body,
                                     self.client.headers)
        return resp, body

    def update_new_service(self, name):
        post_body = {"name": name + "1", "version": "0.1",
                     "full_service_name": name,
                     "service_display_name": name + "1"}
        post_body = json.dumps(post_body)
        resp, body = self.client.put('v1/admin/services/' + name,
                                     post_body, self.client.headers)
        return resp, body

    def delete_service(self, name):
        resp, body = self.client.delete('v1/admin/services/' + name,
                                        self.client.headers)
        return resp, body

    def create_complex_service(self, name):

        post_body = {"name": name, "version": "0.1",
                     "full_service_name": name,
                     "service_display_name": name,
                     "agent": ["CreatePrimaryDC.template",
                               "LeaveDomain.template",
                               "SetPassword.template",
                               "CreateSecondaryDC.template",
                               "AskDnsIp.template",
                               "JoinDomain.template"],
                     "heat": ["RouterInterface.template",
                              "Windows.template",
                              "Network.template",
                              "NNSecurity.template",
                              "Param.template",
                              "Subnet.template",
                              "InstancePortWSubnet.template",
                              "InstancePort.template"],
                     "scripts": ["Install-RoleSecondaryDomainController.ps1",
                                 "Install-RolePrimaryDomainController.ps1",
                                 "Join-Domain.ps1",
                                 "ImportCoreFunctions.ps1",
                                 "Get-DnsListeningIpAddress.ps1",
                                 "Set-LocalUserPassword.ps1"],
                     "ui": ["ActiveDirectory.yaml"],
                     "workflows": ["AD.xml",
                                   "Networking.xml",
                                   "Common.xml"]}
        post_body = json.dumps(post_body)
        resp, body = self.client.put('v1/admin/services/' + name, post_body,
                                     self.client.headers)
        return resp, body, json.loads(post_body)

    def switch_service_parameter(self, service):
        post_body = None
        resp, body = self.client.post('v1/admin/services/%s/toggle_enabled' %
                                      service, post_body, self.client.headers)
        return resp, json.loads(body)

    def reset_cache(self):
        post_body = None
        resp, body = self.client.post('v1/admin/reset_caches', post_body,
                                      self.client.headers)
        return resp, json.loads(body)

    def get_list_of_meta_information_about_service(self, service):
        resp, body = self.client.get('v1/admin/services/%s/info' % service,
                                     self.client.headers)
        return resp, json.loads(body)
