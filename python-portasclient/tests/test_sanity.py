import unittest
import logging
from mock import MagicMock

from portasclient.v1 import Client
import portasclient.v1.environments as environments
import portasclient.v1.services as services
import portasclient.v1.sessions as sessions

LOG = logging.getLogger('Unit tests')

def my_mock(*a, **b):
    return [a, b]

api = MagicMock(json_request=my_mock)

class SanityUnitTests(unittest.TestCase):
    
    def test_create_client_instance(self):

        endpoint =  'http://localhost:8001'
        test_client = Client(endpoint=endpoint, token='1', timeout=10)

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

        assert result.headers == {}
        assert result.body == {'name': 'test'}

    def test_env_manager_delete(self):

        manager = environments.EnvironmentManager(api)

        result = manager.delete('test')

        assert result is None

    def test_env_manager_update(self):

        manager = environments.EnvironmentManager(api)

        result = manager.update('1', 'test')

        assert result.body == {'name': 'test'}

    def test_env_manager_get(self):

        manager = environments.EnvironmentManager(api)

        result = manager.get('test')
        ## WTF?
        assert result.manager is not None

    def test_ad_manager_list(self):

        manager = services.ActiveDirectoryManager(api)

        result = manager.list('datacenter1')

        assert result == []

    def test_ad_manager_create(self):

        manager = services.ActiveDirectoryManager(api)

        result = manager.create('datacenter1', 'session1', 'test')

        assert result.headers == {'X-Configuration-Session': 'session1'}
        assert result.body == 'test'

    #@unittest.skip("https://mirantis.jira.com/browse/KEERO-218")
    def test_ad_manager_delete(self):

        manager = services.ActiveDirectoryManager(api)

        result = manager.delete('datacenter1', 'session1', 'test')

        assert result is None
        
    def test_iis_manager_list(self):

        manager = services.WebServerManager(api)

        result = manager.list('datacenter1')

        assert result == []

    def test_iis_manager_create(self):

        manager = services.WebServerManager(api)

        result = manager.create('datacenter1', 'session1', 'test')

        assert result.headers == {'X-Configuration-Session': 'session1'}
        assert result.body == 'test'

    #@unittest.skip("https://mirantis.jira.com/browse/KEERO-218")
    def test_iis_manager_delete(self):

        manager = services.WebServerManager(api)

        result = manager.delete('datacenter1', 'session1', 'test')

        assert result is None
        
    def test_session_manager_list(self):

        manager = sessions.SessionManager(api)

        result = manager.list('datacenter1')

        assert result == []

    def test_session_manager_delete(self):

        manager = sessions.SessionManager(api)

        result = manager.delete('datacenter1', 'session1')

        assert result is None
        
    def test_session_manager_get(self):

        manager = sessions.SessionManager(api)

        result = manager.get('datacenter1', 'session1')
        # WTF?
        assert result.manager is not None
        
    def test_session_manager_configure(self):

        manager = sessions.SessionManager(api)

        result = manager.configure('datacenter1')

        assert result.headers == {}
        
    def test_session_manager_deploy(self):

        manager = sessions.SessionManager(api)

        result = manager.deploy('datacenter1', '1')

        assert result is None
    
    #@unittest.skip("https://mirantis.jira.com/browse/KEERO-219")
    def test_session_manager_reports(self):

        manager = sessions.SessionManager(api)

        result = manager.reports('datacenter1', '1')

        assert result == []