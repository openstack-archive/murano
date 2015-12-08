# Copyright (c) 2014 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import math

import netaddr
from netaddr.strategy import ipv4
from oslo.utils import uuidutils
import retrying

import murano.common.config as config
from murano.common import exceptions as exc
import murano.dsl.helpers as helpers
import murano.dsl.murano_class as murano_class
import murano.dsl.murano_object as murano_object
from murano.openstack.common import log as logging


LOG = logging.getLogger(__name__)


@murano_class.classname('io.murano.system.NetworkExplorer')
class NetworkExplorer(murano_object.MuranoObject):
    # noinspection PyAttributeOutsideInit
    def initialize(self, _context):
        environment = helpers.get_environment(_context)
        self._clients = environment.clients
        self._tenant_id = environment.tenant_id
        self._settings = config.CONF.networking
        self._available_cidrs = self._generate_possible_cidrs()

    # noinspection PyPep8Naming
    def getDefaultRouter(self, _context):
        return self._get_default_router(_context)

    # NOTE(starodubcevna): to avoid simultaneous router requests we use retry
    # decorator with random delay 1-10 seconds between attempts and maximum
    # delay time 30 seconds.
    @retrying.retry(retry_on_exception=lambda e: isinstance(e,
                    exc.RouterInfoException),
                    wait_random_min=1000, wait_random_max=10000,
                    stop_max_delay=30000)
    def _get_default_router(self, _context):
        client = self._clients.get_neutron_client(_context)
        router_name = self._settings.router_name

        routers = client.list_routers(
            tenant_id=self._tenant_id, name=router_name).get('routers')
        if len(routers) == 0:
            LOG.debug('Router {0} not found'.format(router_name))
            if self._settings.create_router:
                LOG.debug('Attempting to create Router {0}'.
                          format(router_name))
                external_network = self._settings.external_network
                kwargs = {'id': external_network} \
                    if uuidutils.is_uuid_like(external_network) \
                    else {'name': external_network}
                networks = client.list_networks(**kwargs).get('networks')
                ext_nets = filter(lambda n: n['router:external'], networks)
                if len(ext_nets) == 0:
                    raise KeyError('Router %s could not be created, '
                                   'no external network found' % router_name)
                nid = ext_nets[0]['id']

                body_data = {
                    'router': {
                        'name': router_name,
                        'external_gateway_info': {
                            'network_id': nid
                        },
                        'admin_state_up': True,
                    }
                }
                router = client.create_router(body=body_data).get('router')
                LOG.debug('Created router: {0}'.format(router))
                return router['id']
            else:
                raise KeyError('Router %s was not found' % router_name)
        else:
            if routers[0]['external_gateway_info'] is None:
                raise exc.RouterInfoException('Please set external gateway for'
                                              ' the router %s ' % router_name)
            router_id = routers[0]['id']
        return router_id

    # noinspection PyPep8Naming
    def getAvailableCidr(self, _context, routerId, netId):
        """Uses hash of network IDs to minimize the collisions:
        different nets will attempt to pick different cidrs out of available
        range.
        If the cidr is taken will pick another one
        """
        taken_cidrs = self._get_cidrs_taken_by_router(_context, routerId)
        id_hash = hash(netId)
        num_fails = 0
        while num_fails < len(self._available_cidrs):
            cidr = self._available_cidrs[
                (id_hash + num_fails) % len(self._available_cidrs)]
            if any(self._cidrs_overlap(cidr, taken_cidr) for taken_cidr in
                   taken_cidrs):
                num_fails += 1
            else:
                return str(cidr)
        return None

    # noinspection PyPep8Naming
    def getDefaultDns(self):
        return self._settings.default_dns

    # noinspection PyPep8Naming
    def getExternalNetworkIdForRouter(self, _context, routerId):
        client = self._clients.get_neutron_client(_context)
        router = client.show_router(routerId).get('router')
        if not router or 'external_gateway_info' not in router:
            return None
        return router['external_gateway_info'].get('network_id')

    # noinspection PyPep8Naming
    def getExternalNetworkIdForNetwork(self, _context, networkId):
        client = self._clients.get_neutron_client(_context)
        network = client.show_network(networkId).get('network')
        if network.get('router:external', False):
            return networkId

        # Get router interfaces of the network
        router_ports = client.list_ports(
            **{'device_owner': 'network:router_interface',
               'network_id': networkId}).get('ports')

        # For each router this network is connected to
        # check if the router has external_gateway set
        for router_port in router_ports:
            ext_net_id = self.getExternalNetworkIdForRouter(
                _context,
                router_port.get('device_id'))
            if ext_net_id:
                return ext_net_id
        return None

    def _get_cidrs_taken_by_router(self, _context, router_id):
        if not router_id:
            return []
        client = self._clients.get_neutron_client(_context)
        ports = client.list_ports(device_id=router_id)['ports']
        subnet_ids = []
        for port in ports:
            for fixed_ip in port['fixed_ips']:
                subnet_ids.append(fixed_ip['subnet_id'])

        all_subnets = client.list_subnets()['subnets']
        filtered_cidrs = [netaddr.IPNetwork(subnet['cidr']) for subnet in
                          all_subnets if subnet['id'] in subnet_ids]

        return filtered_cidrs

    @staticmethod
    def _cidrs_overlap(cidr1, cidr2):
        return (cidr1 in cidr2) or (cidr2 in cidr1)

    def _generate_possible_cidrs(self):
        bits_for_envs = int(
            math.ceil(math.log(self._settings.max_environments, 2)))
        bits_for_hosts = int(math.ceil(math.log(self._settings.max_hosts, 2)))
        width = ipv4.width
        mask_width = width - bits_for_hosts - bits_for_envs
        net = netaddr.IPNetwork(
            '{0}/{1}'.format(self._settings.env_ip_template, mask_width))
        return list(net.subnet(width - bits_for_hosts))

    # noinspection PyPep8Naming
    def listNetworks(self, _context):
        client = self._clients.get_neutron_client(_context)
        return client.list_networks()['networks']

    # noinspection PyPep8Naming
    def listSubnetworks(self, _context):
        client = self._clients.get_neutron_client(_context)
        return client.list_subnets()['subnets']

    # noinspection PyPep8Naming
    def listPorts(self, _context):
        client = self._clients.get_neutron_client(_context)
        return client.list_ports()['ports']
