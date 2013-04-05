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

import unittest
import logging
from mock import MagicMock

from glazierclient.client import Client
import glazierclient.v1.environments as environments
import glazierclient.v1.services as services
import glazierclient.v1.sessions as sessions

def my_mock(*a, **b):
    return [a, b]

LOG = logging.getLogger('Unit tests')
api = MagicMock(json_request=my_mock)


class UnitTestsForClassesAndFunctions(unittest.TestCase):
    
    def test_create_client_instance(self):

        endpoint = 'http://no-resolved-host:8001'
        test_client = Client('1', endpoint=endpoint, token='1', timeout=10)

        assert test_client.environments is not None
        assert test_client.sessions is not None
        assert test_client.activeDirectories is not None
        assert test_client.webServers is not None

    def test_env_manager_list(self):
        manager = environments.EnvironmentManager(api)
        result = manager.list()
        assert result == []

    def test_env_manager_create(self):
        manager = environments.EnvironmentManager(api)
        result = manager.create('test')
        assert result.body == {'name': 'test'}

    def test_env_manager_create_with_named_parameters(self):
        manager = environments.EnvironmentManager(api)
        result = manager.create(name='test')
        assert result.body == {'name': 'test'}

    def test_env_manager_create_negative_without_parameters(self):
        result = 'Exception'
        manager = environments.EnvironmentManager(api)
        try:
            result = manager.create()
        except TypeError:
            pass
        assert result is 'Exception'

    def test_env_manager_delete(self):
        manager = environments.EnvironmentManager(api)
        result = manager.delete('test')
        assert result is None

    def test_env_manager_delete_with_named_parameters(self):
        manager = environments.EnvironmentManager(api)
        result = manager.delete(environment_id='1')
        assert result is None

    def test_env_manager_delete_negative_without_parameters(self):
        result = 'Exception'
        manager = environments.EnvironmentManager(api)
        try:
            result = manager.delete()
        except TypeError:
            pass
        assert result is 'Exception'

    def test_env_manager_update(self):
        manager = environments.EnvironmentManager(api)
        result = manager.update('1', 'test')
        assert result.body == {'name': 'test'}

    def test_env_manager_update_with_named_parameters(self):
        manager = environments.EnvironmentManager(api)
        result = manager.update(environment_id='1',
                                name='test')
        assert result.body == {'name': 'test'}

    def test_env_manager_update_negative_with_one_parameter(self):
        result = 'Exception'
        manager = environments.EnvironmentManager(api)
        try:
            result = manager.update('test')
        except TypeError:
            pass
        assert result is 'Exception'

    def test_env_manager_update_negative_without_parameters(self):
        result = 'Exception'
        manager = environments.EnvironmentManager(api)
        try:
            result = manager.update()
        except TypeError:
            pass
        assert result is 'Exception'

    def test_env_manager_get(self):
        manager = environments.EnvironmentManager(api)
        result = manager.get('test')
        ## WTF?
        assert result.manager is not None
        
    def test_env(self):
        environment = environments.Environment(api, api)
        assert environment.data() is not None

    def test_ad_manager_list_with_one_parameter(self):
        manager = services.ActiveDirectoryManager(api)
        result = manager.list('datacenter1')
        assert result == []

    def test_ad_manager_list_with_all_parameters(self):
        manager = services.ActiveDirectoryManager(api)
        result = manager.list('test', '1')
        assert result == []

    def test_ad_manager_list_with_named_parameters(self):
        manager = services.ActiveDirectoryManager(api)
        result = manager.list(environment_id='test', session_id='1')
        assert result == []

    def test_ad_manager_list_with_named_parameter(self):
        manager = services.ActiveDirectoryManager(api)
        result = manager.list(environment_id='test')
        assert result == []

    def test_ad_manager_list_negative_without_parameters(self):
        result = 'Exception'
        manager = services.ActiveDirectoryManager(api)
        try:
            result = manager.list()
        except TypeError:
            pass
        assert result is 'Exception'

    def test_ad_manager_create(self):
        manager = services.ActiveDirectoryManager(api)
        result = manager.create('datacenter1', 'session1', 'test')
        assert result.headers == {'X-Configuration-Session': 'session1'}
        assert result.body == 'test'

    def test_ad_manager_create_with_named_parameters(self):
        manager = services.ActiveDirectoryManager(api)
        result = manager.create(environment_id='datacenter1',
                                session_id='session2',
                                active_directory='test2')
        assert result.headers == {'X-Configuration-Session': 'session2'}
        assert result.body == 'test2'

    def test_ad_manager_create_negative_with_two_parameters(self):
        result = 'Exception'
        manager = services.ActiveDirectoryManager(api)
        try:
            result = manager.create('datacenter1', 'session1')
        except TypeError:
            pass
        assert result is 'Exception'

    def test_ad_manager_create_negative_with_one_parameter(self):
        result = 'Exception'
        manager = services.ActiveDirectoryManager(api)
        try:
            result = manager.create('datacenter1')
        except TypeError:
            pass
        assert result is 'Exception'

    def test_ad_manager_create_negative_without_parameters(self):
        result = 'Exception'
        manager = services.ActiveDirectoryManager(api)
        try:
            result = manager.create()
        except TypeError:
            pass
        assert result is 'Exception'

    def test_ad_manager_delete(self):
        manager = services.ActiveDirectoryManager(api)
        result = manager.delete('datacenter1', 'session1', 'test')
        assert result is None

    def test_ad_manager_delete_with_named_parameters(self):
        manager = services.ActiveDirectoryManager(api)
        result = manager.delete(environment_id='datacenter1',
                                session_id='session1',
                                service_id='test')
        assert result is None

    def test_ad_manager_delete_negative_with_two_parameters(self):
        result = 'Exception'
        manager = services.ActiveDirectoryManager(api)
        try:
            result = manager.delete('datacenter1', 'session1')
        except TypeError:
            pass
        assert result == 'Exception'

    def test_ad_manager_delete_negative_with_one_parameter(self):
        result = 'Exception'
        manager = services.ActiveDirectoryManager(api)
        try:
            result = manager.delete('datacenter1')
        except TypeError:
            pass
        assert result == 'Exception'

    def test_ad_manager_delete_negative_without_parameters(self):
        result = 'Exception'
        manager = services.ActiveDirectoryManager(api)
        try:
            result = manager.delete()
        except TypeError:
            pass
        assert result == 'Exception'
        
    def test_iis_manager_list_with_one_parameter(self):
        manager = services.WebServerManager(api)
        result = manager.list('datacenter1')
        assert result == []

    def test_iis_manager_list_with_named_parameter(self):
        manager = services.WebServerManager(api)
        result = manager.list(environment_id='datacenter1')
        assert result == []

    def test_iis_manager_list_with_all_parameters(self):
        manager = services.WebServerManager(api)
        result = manager.list('test', '1')
        assert result == []

    def test_iis_manager_list_with_named_parameters(self):
        manager = services.WebServerManager(api)
        result = manager.list(environment_id='test',
                              session_id='1')
        assert result == []

    def test_iis_manager_list_negative_without_parameters(self):
        result = 'Exception'
        manager = services.WebServerManager(api)
        try:
            result = manager.list()
        except TypeError:
            pass
        assert result == 'Exception'

    def test_iis_manager_create(self):
        manager = services.WebServerManager(api)
        result = manager.create('datacenter1', 'session1', 'test')
        assert result.headers == {'X-Configuration-Session': 'session1'}
        assert result.body == 'test'

    def test_iis_manager_create_with_named_parameters(self):
        manager = services.WebServerManager(api)
        result = manager.create(environment_id='datacenter',
                                session_id='session',
                                web_server='test2')
        assert result.headers == {'X-Configuration-Session': 'session'}
        assert result.body == 'test2'

    def test_iis_manager_create_negative_with_two_parameters(self):
        result = 'Exception'
        manager = services.WebServerManager(api)
        try:
            result = manager.create('datacenter1', 'session1')
        except TypeError:
            pass
        assert result == 'Exception'

    def test_iis_manager_create_negative_with_one_parameter(self):
        result = 'Exception'
        manager = services.WebServerManager(api)
        try:
            result = manager.create('datacenter1')
        except TypeError:
            pass
        assert result == 'Exception'

    def test_iis_manager_create_negative_without_parameters(self):
        result = 'Exception'
        manager = services.WebServerManager(api)
        try:
            result = manager.create()
        except TypeError:
            pass
        assert result == 'Exception'

    def test_iis_manager_delete(self):
        manager = services.WebServerManager(api)
        result = manager.delete('datacenter1', 'session1', 'test')
        assert result is None

    def test_iis_manager_delete_with_named_parameters(self):
        manager = services.WebServerManager(api)
        result = manager.delete(environment_id='datacenter',
                                session_id='session',
                                service_id='test')
        assert result is None

    def test_iis_manager_delete_negative_with_two_parameters(self):
        result = 'Exception'
        manager = services.WebServerManager(api)
        try:
            result = manager.delete('datacenter1', 'session1')
        except TypeError:
            pass
        assert result == 'Exception'

    def test_iis_manager_delete_negative_with_one_parameter(self):
        result = 'Exception'
        manager = services.WebServerManager(api)
        try:
            result = manager.delete('datacenter1')
        except TypeError:
            pass
        assert result == 'Exception'

    def test_iis_manager_delete_negative_without_parameters(self):
        result = 'Exception'
        manager = services.WebServerManager(api)
        try:
            result = manager.delete()
        except TypeError:
            pass
        assert result == 'Exception'

    def test_service_ad(self):
        service_ad = services.ActiveDirectory(api, api)
        assert service_ad.data() is not None
    
    def test_service_iis(self):
        service_iis = services.ActiveDirectory(api, api)
        assert service_iis.data() is not None
        
    def test_session_manager_list(self):
        manager = sessions.SessionManager(api)
        result = manager.list('datacenter1')
        assert result == []

    def test_session_manager_list_with_named_parameters(self):
        manager = sessions.SessionManager(api)
        result = manager.list(environment_id='datacenter1')
        assert result == []

    def test_session_manager_list_negative_without_parameters(self):
        result = 'Exception'
        manager = sessions.SessionManager(api)
        try:
            result = manager.list()
        except TypeError:
            pass
        assert result == 'Exception'

    def test_session_manager_delete(self):
        manager = sessions.SessionManager(api)
        result = manager.delete('datacenter1', 'session1')
        assert result is None

    def test_session_manager_delete_with_named_parameters(self):
        manager = sessions.SessionManager(api)
        result = manager.delete(environment_id='datacenter1',
                                session_id='session1')
        assert result is None

    def test_session_manager_delete_negative_with_one_parameter(self):
        result = 'Exception'
        manager = sessions.SessionManager(api)
        try:
            result = manager.delete('datacenter1')
        except TypeError:
            pass
        assert result == 'Exception'

    def test_session_manager_delete_negative_without_parameters(self):
        result = 'Exception'
        manager = sessions.SessionManager(api)
        try:
            result = manager.delete()
        except TypeError:
            pass
        assert result == 'Exception'
        
    def test_session_manager_get(self):
        manager = sessions.SessionManager(api)
        result = manager.get('datacenter1', 'session1')
        # WTF?
        assert result.manager is not None
        
    def test_session_manager_configure(self):
        manager = sessions.SessionManager(api)
        result = manager.configure('datacenter1')
        assert result is not None

    def test_session_manager_configure_with_named_parameter(self):
        manager = sessions.SessionManager(api)
        result = manager.configure(environment_id='datacenter1')
        assert result is not None

    def test_session_manager_configure_negative_without_parameters(self):
        result = 'Exception'
        manager = sessions.SessionManager(api)
        try:
            result = manager.configure()
        except TypeError:
            pass
        assert result == 'Exception'

    def test_session_manager_deploy(self):
        manager = sessions.SessionManager(api)
        result = manager.deploy('datacenter1', '1')
        assert result is None

    def test_session_manager_deploy_with_named_parameters(self):
        manager = sessions.SessionManager(api)
        result = manager.deploy(environment_id='datacenter1',
                                session_id='1')
        assert result is None

    def test_session_manager_deploy_negative_with_one_parameter(self):
        result = 'Exception'
        manager = sessions.SessionManager(api)
        try:
            result = manager.deploy('datacenter1')
        except TypeError:
            pass
        assert result == 'Exception'

    def test_session_manager_deploy_negative_without_parameters(self):
        result = 'Exception'
        manager = sessions.SessionManager(api)
        try:
            result = manager.deploy()
        except TypeError:
            pass
        assert result == 'Exception'

    def test_session_manager_reports(self):
        manager = sessions.SessionManager(api)
        result = manager.reports('datacenter1', '1')
        assert result == []

    def test_session_manager_reports_with_named_parameters(self):
        manager = sessions.SessionManager(api)
        result = manager.reports(environment_id='datacenter1',
                                 session_id='1')
        assert result == []

    def test_session_manager_reports_negative_with_one_parameter(self):
        result = 'Exception'
        manager = sessions.SessionManager(api)
        try:
            result = manager.reports('datacenter1')
        except TypeError:
            pass
        assert result == 'Exception'

    def test_session_manager_reports_negative_without_parameters(self):
        result = 'Exception'
        manager = sessions.SessionManager(api)
        try:
            result = manager.reports()
        except TypeError:
            pass
        assert result == 'Exception'
