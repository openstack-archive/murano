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
from httpretty import HTTPretty, httprettified
from glazierclient.client import Client


LOG = logging.getLogger('Unit tests')


class UnitTestsForClassesAndFunctions(unittest.TestCase):

    @httprettified
    def test_client_env_list_with_empty_list(self):
        HTTPretty.register_uri(HTTPretty.GET,
                               "http://no-resolved-host:8001/environments",
                               body='{"environments": []}',
                               adding_headers={
                               'Content-Type': 'application/json',})
        endpoint =  'http://no-resolved-host:8001'
        test_client = Client('1', endpoint=endpoint, token='1', timeout=10)

        result = test_client.environments.list()
        assert result == []

    @httprettified
    def test_client_env_list_with_elements(self):
        body = ('{"environments":['
                '{"id": "0ce373a477f211e187a55404a662f968",'
                '"name": "dc1",'
                '"created": "2010-11-30T03:23:42Z",'
                '"updated": "2010-11-30T03:23:44Z",'
                '"tenant-id": "0849006f7ce94961b3aab4e46d6f229a"},'
                '{"id": "0ce373a477f211e187a55404a662f961",'
                '"name": "dc2",'
                '"created": "2010-11-30T03:23:42Z",'
                '"updated": "2010-11-30T03:23:44Z",'
                '"tenant-id": "0849006f7ce94961b3aab4e4626f229a"}'
                ']}')
        HTTPretty.register_uri(HTTPretty.GET,
                               "http://no-resolved-host:8001/environments",
                               body=body,
                               adding_headers={
                               'Content-Type': 'application/json',})
        endpoint =  'http://no-resolved-host:8001'
        test_client = Client('1', endpoint=endpoint, token='1', timeout=10)

        result = test_client.environments.list()
        assert result[0].name == 'dc1'
        assert result[-1].name == 'dc2'

    @httprettified
    def test_client_env_create(self):
        body = ('{"id": "0ce373a477f211e187a55404a662f968",'
                  '"name": "test",'
                  '"created": "2010-11-30T03:23:42Z",'
                  '"updated": "2010-11-30T03:23:44Z",'
                  '"tenant-id": "0849006f7ce94961b3aab4e46d6f229a"}'
                  )
        HTTPretty.register_uri(HTTPretty.POST,
                               "http://no-resolved-host:8001/environments",
                               body=body,
                               adding_headers={
                               'Content-Type': 'application/json',})
        endpoint =  'http://no-resolved-host:8001'
        test_client = Client('1', endpoint=endpoint, token='1', timeout=10)

        result = test_client.environments.create('test')
        assert result.name == 'test'

    @httprettified
    def test_client_ad_list(self):
        body = ('{"activeDirectories": [{'
                '"id": "1",'
                '"name": "dc1",'
                '"created": "2010-11-30T03:23:42Z",'
                '"updated": "2010-11-30T03:23:44Z",'
                '"configuration": "standalone",'
                '"units": [{'
                '"id": "0ce373a477f211e187a55404a662f961",'
                '"type": "master",'
                '"location": "test"}]}]}')
        url = ("http://no-resolved-host:8001/environments"
               "/1/activeDirectories")
        HTTPretty.register_uri(HTTPretty.GET, url,
                               body=body,
                               adding_headers={
                               'Content-Type': 'application/json',})
        endpoint =  'http://no-resolved-host:8001'
        test_client = Client('1', endpoint=endpoint, token='1', timeout=10)

        result = test_client.activeDirectories.list('1', 'test')
        assert result[0].name == 'dc1'

    @httprettified
    def test_client_ad_create(self):
        body = ('{'
                '"id": "1",'
                '"name": "ad1",'
                '"created": "2010-11-30T03:23:42Z",'
                '"updated": "2010-11-30T03:23:44Z",'
                '"configuration": "standalone",'
                '"units": [{'
                '"id": "0ce373a477f211e187a55404a662f961",'
                '"type": "master",'
                '"location": "test"}]}')
        url = ("http://no-resolved-host:8001/environments"
               "/1/activeDirectories")
        HTTPretty.register_uri(HTTPretty.POST, url,
                               body=body,
                               adding_headers={
                               'Content-Type': 'application/json',})
        endpoint =  'http://no-resolved-host:8001'
        test_client = Client('1', endpoint=endpoint, token='1', timeout=10)

        result = test_client.activeDirectories.create('1', 'test', 'ad1')
        assert result.name == 'ad1'

    @httprettified
    def test_client_ad_list_without_elements(self):
        body = ('{"activeDirectories": []}')
        url = ("http://no-resolved-host:8001/environments"
               "/1/activeDirectories")
        HTTPretty.register_uri(HTTPretty.GET, url,
                               body=body,
                               adding_headers={
                               'Content-Type': 'application/json',})
        endpoint =  'http://no-resolved-host:8001'
        test_client = Client('1', endpoint=endpoint, token='1', timeout=10)

        result = test_client.activeDirectories.list('1', 'test')
        assert result == []

    @httprettified
    def test_client_iis_list(self):
        body = ('{"webServers": [{'
                '"id": "1",'
                '"name": "iis11",'
                '"created": "2010-11-30T03:23:42Z",'
                '"updated": "2010-11-30T03:23:44Z",'
                '"domain": "acme",'
                '"units": [{'
                '"id": "0ce373a477f211e187a55404a662f961",'
                '"endpoint": {"host": "1.1.1.1"},'
                '"location": "test"}]}]}')
        url = ("http://no-resolved-host:8001/environments"
               "/1/webServers")
        HTTPretty.register_uri(HTTPretty.GET, url,
                               body=body,
                               adding_headers={
                               'Content-Type': 'application/json',})
        endpoint =  'http://no-resolved-host:8001'
        test_client = Client('1', endpoint=endpoint, token='1', timeout=10)

        result = test_client.webServers.list('1', 'test')
        assert result[0].name == 'iis11'

    @httprettified
    def test_client_iis_create(self):
        body = ('{'
                '"id": "1",'
                '"name": "iis12",'
                '"created": "2010-11-30T03:23:42Z",'
                '"updated": "2010-11-30T03:23:44Z",'
                '"domain": "acme",'
                '"units": [{'
                '"id": "0ce373a477f211e187a55404a662f961",'
                '"endpoint": {"host": "1.1.1.1"},'
                '"location": "test"}]}')
        url = ("http://no-resolved-host:8001/environments"
               "/1/webServers")
        HTTPretty.register_uri(HTTPretty.POST, url,
                               body=body,
                               adding_headers={
                               'Content-Type': 'application/json',})
        endpoint =  'http://no-resolved-host:8001'
        test_client = Client('1', endpoint=endpoint, token='1', timeout=10)

        result = test_client.webServers.create('1', 'test', 'iis12')
        assert result.name == 'iis12'

    @httprettified
    def test_client_iis_list_without_elements(self):
        body = ('{"webServers": []}')
        url = ("http://no-resolved-host:8001/environments"
               "/1/webServers")
        HTTPretty.register_uri(HTTPretty.GET, url,
                               body=body,
                               adding_headers={
                               'Content-Type': 'application/json',})
        endpoint =  'http://no-resolved-host:8001'
        test_client = Client('1', endpoint=endpoint, token='1', timeout=10)

        result = test_client.webServers.list('1', 'test')
        assert result == []
