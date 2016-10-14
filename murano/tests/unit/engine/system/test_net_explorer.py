# Copyright (c) 2016 AT&T
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

import mock

from oslo_config import cfg

from murano.dsl import murano_method
from murano.dsl import murano_type
from murano.engine.system import net_explorer
from murano.tests.unit import base

CONF = cfg.CONF


class TestNetExplorer(base.MuranoTestCase):
    def setUp(self):
        super(TestNetExplorer, self).setUp()
        self.mock_class = mock.MagicMock(spec=murano_type.MuranoClass)
        self.mock_method = mock.MagicMock(spec=murano_method.MuranoMethod)

        self._this = mock.MagicMock()
        self.region_name = "test-region"

        self.addCleanup(mock.patch.stopall)

    @mock.patch("murano.engine.system.net_explorer.nclient")
    @mock.patch("murano.engine.system.net_explorer.auth_utils")
    @mock.patch("murano.dsl.helpers.get_execution_session")
    def test_get_available_cidr(self, execution_session,
                                mock_authentication, mock_nclient):
        ne = net_explorer.NetworkExplorer(self._this, self.region_name)
        router_id = 12
        net_id = 144
        self.assertIsNotNone(ne.get_available_cidr(router_id, net_id))
        self.assertTrue(execution_session.called)

    @mock.patch("murano.engine.system.net_explorer.nclient")
    @mock.patch("murano.engine.system.net_explorer.auth_utils")
    @mock.patch("murano.dsl.helpers.get_execution_session")
    def test_list(self, execution_session, mock_authentication, mock_nclient):
        ne = net_explorer.NetworkExplorer(self._this, self.region_name)
        self.assertEqual(ne.list_networks(),
                         ne._client.list_networks()['networks'])
        self.assertEqual(ne.list_subnetworks(),
                         ne._client.list_subnets()['subnets'])
        self.assertEqual(ne.list_ports(), ne._client.list_ports()['ports'])
        self.assertEqual(ne.list_neutron_extensions(),
                         ne._client.list_extensions()['extensions'])
        self.assertEqual(ne.get_default_dns(), ne._settings.default_dns)

    @mock.patch("murano.engine.system.net_explorer.nclient")
    @mock.patch("murano.engine.system.net_explorer.auth_utils")
    @mock.patch("murano.dsl.helpers.get_execution_session")
    def test_get_router_error(self, execution_session,
                              mock_authentication, mock_nclient):
        ne = net_explorer.NetworkExplorer(self._this, self.region_name)
        self.assertRaises(KeyError, ne.get_default_router)

    @mock.patch("murano.engine.system.net_explorer.nclient")
    @mock.patch("murano.engine.system.net_explorer.auth_utils")
    @mock.patch("murano.dsl.helpers.get_execution_session")
    def test_get_ext_network_id_router(self, execution_session,
                                       mock_authentication, mock_nclient):
        ne = net_explorer.NetworkExplorer(self._this, self.region_name)
        router_id = 12
        self.assertIsNone(ne.get_external_network_id_for_router(router_id))

    @mock.patch("murano.engine.system.net_explorer.nclient")
    @mock.patch("murano.engine.system.net_explorer.auth_utils")
    @mock.patch("murano.dsl.helpers.get_execution_session")
    def test_get_ext_network_id_network(self, execution_session,
                                        mock_authentication, mock_nclient):
        ne = net_explorer.NetworkExplorer(self._this, self.region_name)
        net_id = 144
        self.assertEqual(net_id,
                         ne.get_external_network_id_for_network(net_id))

    @mock.patch("murano.engine.system.net_explorer.nclient")
    @mock.patch("murano.engine.system.net_explorer.auth_utils")
    @mock.patch("murano.dsl.helpers.get_execution_session")
    def test_get_cidr_none_router(self, execution_session,
                                  mock_authentication, mock_nclient):
        ne = net_explorer.NetworkExplorer(self._this, self.region_name)
        router_id = None
        self.assertEqual([], ne._get_cidrs_taken_by_router(router_id))
