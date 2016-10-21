# Copyright (c) 2016 Mirantis, Inc.
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

import requests
import socket
import time

from tempest.clients import Manager as services_manager
from tempest.common import credentials_factory as common_creds
from tempest.common import dynamic_creds
from tempest.common import waiters
from tempest import config
from tempest.lib import base
from tempest.lib import exceptions

from murano_tempest_tests import clients
from murano_tempest_tests import utils

CONF = config.CONF


class BaseApplicationCatalogScenarioTest(base.BaseTestCase):
    """Base test class for Murano Application Catalog Scenario tests."""

    @classmethod
    def setUpClass(cls):
        super(BaseApplicationCatalogScenarioTest, cls).setUpClass()
        cls.resource_setup()

    @classmethod
    def tearDownClass(cls):
        cls.resource_cleanup()
        super(BaseApplicationCatalogScenarioTest, cls).tearDownClass()

    @classmethod
    def get_client_with_isolated_creds(cls, type_of_creds="admin"):

        creds = cls.get_configured_isolated_creds(type_of_creds=type_of_creds)

        os = clients.Manager(credentials=creds)
        client = os.application_catalog_client

        return client

    @classmethod
    def get_configured_isolated_creds(cls, type_of_creds='admin'):
        identity_version = CONF.identity.auth_version
        if identity_version == 'v3':
            cls.admin_role = CONF.identity.admin_role
        else:
            cls.admin_role = 'admin'
        if not hasattr(cls, 'dynamic_cred'):
            cls.dynamic_cred = dynamic_creds.DynamicCredentialProvider(
                identity_version=CONF.identity.auth_version,
                name=cls.__name__, admin_role=cls.admin_role,
                admin_creds=common_creds.get_configured_admin_credentials(
                    'identity_admin'))
        if type_of_creds == 'primary':
            creds = cls.dynamic_cred.get_primary_creds()
        elif type_of_creds == 'admin':
            creds = cls.dynamic_cred.get_admin_creds()
        elif type_of_creds == 'alt':
            creds = cls.dynamic_cred.get_alt_creds()
        else:
            creds = cls.dynamic_cred.get_credentials(type_of_creds)
        cls.dynamic_cred.type_of_creds = type_of_creds

        return creds.credentials

    @classmethod
    def verify_nonempty(cls, *args):
        if not all(args):
            msg = "Missing API credentials in configuration."
            raise cls.skipException(msg)

    @classmethod
    def resource_setup(cls):
        if not CONF.service_available.murano:
            skip_msg = "Murano is disabled"
            raise cls.skipException(skip_msg)
        if not hasattr(cls, "os"):
            creds = cls.get_configured_isolated_creds(type_of_creds='primary')
            cls.os = clients.Manager(credentials=creds)
            cls.services_manager = services_manager(creds)

        cls.linux_image = CONF.application_catalog.linux_image
        cls.application_catalog_client = cls.os.application_catalog_client
        cls.artifacts_client = cls.os.artifacts_client
        cls.servers_client = cls.services_manager.servers_client
        cls.orchestration_client = cls.services_manager.orchestration_client
        cls.snapshots_client = cls.services_manager.snapshots_v2_client
        cls.volumes_client = cls.services_manager.volumes_v2_client
        cls.backups_client = cls.services_manager.backups_v2_client
        cls.images_client = cls.services_manager.image_client_v2
        cls.cirros_image = cls.get_required_image_name()

    @classmethod
    def get_required_image_name(cls):
        image = cls.images_client.show_image(CONF.compute.image_ref)
        return image['name']

    @classmethod
    def resource_cleanup(cls):
        cls.clear_isolated_creds()

    @classmethod
    def clear_isolated_creds(cls):
        if hasattr(cls, "dynamic_cred"):
            cls.dynamic_cred.clear_creds()

    def environment_delete(self, environment_id, timeout=180):
        self.application_catalog_client.delete_environment(environment_id)

        start_time = time.time()
        while time.time() - start_time > timeout:
            try:
                self.application_catalog_client.get_environment(environment_id)
            except exceptions.NotFound:
                return

    @classmethod
    def purge_stacks(cls):
        stacks = cls.orchestration_client.list_stacks()['stacks']
        for stack in stacks:
            cls.orchestration_client.delete_stack(stack['id'])
            cls.orchestration_client.wait_for_stack_status(stack['id'],
                                                           'DELETE_COMPLETE')

    def get_service(self, environment, session, service_name):
        for service in self.application_catalog_client.get_services_list(
                environment, session):
            if service['name'] == service_name:
                return service

    def get_stack_id(self, environment_id):
        stacks = self.orchestration_client.list_stacks()['stacks']
        for stack in stacks:
            if environment_id in self.orchestration_client.show_stack(
                    stack['id'])['stack']['description']:
                return stack['id']

    def get_stack_template(self, stack):
        return self.orchestration_client.show_template(stack)

    def get_instance_id(self, name):
        instance_list = self.servers_client.list_servers()['servers']
        for instance in instance_list:
            if name in instance['name']:
                return instance['id']

    def apache(
            self, attributes=None, userName=None, flavor='m1.small'):
        post_body = {
            "instance": {
                "flavor": flavor,
                "image": self.linux_image,
                "assignFloatingIp": True,
                "availabilityZone": "nova",
                "volumes": attributes,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": utils.generate_uuid()
                },
                "name": utils.generate_name("testMurano")
            },
            "name": utils.generate_name("ApacheHTTPServer"),
            "userName": userName,
            "?": {
                "_{id}".format(id=utils.generate_uuid()): {
                    "name": "ApacheHTTPServer"
                },
                "type": "io.murano.apps.test.ApacheHttpServerCustom",
                "id": utils.generate_uuid()
            }
        }
        return post_body

    def vm_cinder(
            self, attributes=None, userName=None, flavor='m1.small'):
        post_body = {
            "instance": {
                "flavor": flavor,
                "image": self.cirros_image,
                "assignFloatingIp": True,
                "availabilityZone": "nova",
                "volumes": attributes,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": utils.generate_uuid()
                },
                "name": utils.generate_name("testMurano")
            },
            "name": utils.generate_name("VM"),
            "userName": userName,
            "?": {
                "_{id}".format(id=utils.generate_uuid()): {
                    "name": "VM"
                },
                "type": "io.murano.apps.test.VM",
                "id": utils.generate_uuid()
            }
        }
        return post_body

    def update_executor(self, flavor='m1.small'):
        post_body = {
            "instance": {
                "flavor": flavor,
                "image": self.linux_image,
                "assignFloatingIp": True,
                "?": {
                    "type": "io.murano.resources.LinuxMuranoInstance",
                    "id": utils.generate_uuid()
                },
                "name": utils.generate_name('testMurano')
            },
            "name": utils.generate_name('dummy'),
            "?": {
                "type": "io.murano.apps.test.UpdateExecutor",
                "id": utils.generate_uuid()
            }
        }
        return post_body

    def deploy_environment(self, environment, session):
        self.application_catalog_client.deploy_session(environment['id'],
                                                       session['id'])
        timeout = 1800
        deployed_env = utils.wait_for_environment_deploy(
            self.application_catalog_client, environment['id'],
            timeout=timeout)
        if deployed_env['status'] == 'ready':
            return deployed_env
        elif deployed_env['status'] == 'deploying':
            self.fail('Environment deployment is not finished in {} seconds'.
                      format(timeout))
        else:
            self.fail('Environment has status {}'.format(
                deployed_env['status']))

    def status_check(self, environment_id, configurations):
        for configuration in configurations:
            inst_name = configuration[0]
            ports = configuration[1:]
            ip = self.get_ip_by_instance_name(environment_id, inst_name)
            if ip and ports:
                for port in ports:
                    self.check_port_access(ip, port)
            else:
                self.fail('Instance does not have floating IP')

    def check_path(self, environment_id, path, inst_name=None):
        environment = self.application_catalog_client.\
            get_environment(environment_id)
        if inst_name:
            ip = self.get_ip_by_instance_name(environment_id, inst_name)
        else:
            ip = environment.services[0]['instance']['floatingIpAddress']
        resp = requests.get('http://{0}/{1}'.format(ip, path))
        if resp.status_code == 200:
            return resp
        else:
            self.fail("Service path unavailable")

    def get_ip_by_instance_name(self, environment_id, inst_name):
        for service in self.application_catalog_client.\
                get_services_list(environment_id):
            if inst_name in service['instance']['name']:
                return service['instance']['floatingIpAddress']

    def check_port_access(self, ip, port):
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

    @classmethod
    def create_volume(cls, **kwargs):
        volume = cls.volumes_client.create_volume(**kwargs)['volume']
        waiters.wait_for_volume_status(cls.volumes_client,
                                       volume['id'], 'available')
        return volume['id']

    @classmethod
    def delete_volume(cls, volume_id):
        cls.volumes_client.delete_volume(volume_id)
        is_volume_deleted = False
        while not is_volume_deleted:
            is_volume_deleted = cls.volumes_client.\
                is_resource_deleted(volume_id)
            time.sleep(1)

    def create_snapshot(self, volume_id):
        snapshot = self.snapshots_client.\
            create_snapshot(volume_id=volume_id)['snapshot']
        waiters.wait_for_snapshot_status(self.snapshots_client,
                                         snapshot['id'], 'available')
        return snapshot['id']

    def delete_snapshot(self, snapshot_id):
        self.snapshots_client.delete_snapshot(snapshot_id)
        is_snapshot_deleted = False
        while not is_snapshot_deleted:
            is_snapshot_deleted = self.snapshots_client.\
                is_resource_deleted(snapshot_id)
            time.sleep(1)

    def create_backup(self, volume_id):
        backup = self.backups_client.create_backup(
            volume_id=volume_id,
            force=True)['backup']
        waiters.wait_for_backup_status(self.backups_client,
                                       backup['id'], 'available')
        return backup['id']

    def delete_backup(self, backup_id):
        self.backups_client.delete_backup(backup_id)
        return self.backups_client.wait_for_resource_deletion(backup_id)

    def get_volume(self, environment_id):
        stack = self.get_stack_id(environment_id)
        stack_outputs = self.orchestration_client.\
            show_stack(stack)['stack']['outputs']
        for output in stack_outputs:
            if 'vol' in output['output_key']:
                volume_id = output['output_value']
                return self.volumes_client.show_volume(volume_id)['volume']

    def check_volume_attached(self, name, volume_id):
        instance_id = self.get_instance_id(name)
        attached_volumes = self.servers_client.\
            list_volume_attachments(instance_id)['volumeAttachments']
        assert attached_volumes[0]['id'] == volume_id


class BaseApplicationCatalogScenarioIsolatedAdminTest(
        BaseApplicationCatalogScenarioTest):

    @classmethod
    def resource_setup(cls):
        creds = cls.get_configured_isolated_creds(type_of_creds='admin')
        cls.os = clients.Manager(credentials=creds)
        cls.services_manager = services_manager(creds)
        super(BaseApplicationCatalogScenarioIsolatedAdminTest, cls).\
            resource_setup()
