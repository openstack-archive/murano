# Copyright 2012 OpenStack LLC.
# All Rights Reserved
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
#
# vim: tabstop=4 shiftwidth=4 softtabstop=4
"""
OpenStack Client interface. Handles the REST calls and responses.
"""

import httplib2
import copy
import logging
import json

from . import exceptions
from . import utils
from .service_catalog import ServiceCatalog


logger = logging.getLogger(__name__)


class HTTPClient(httplib2.Http):

    USER_AGENT = 'python-balancerclient'

    def __init__(self, endpoint=None, token=None, username=None,
                 password=None, tenant_name=None, tenant_id=None,
                 region_name=None, auth_url=None, auth_tenant_id=None,
                 timeout=600, insecure=False):
        super(HTTPClient, self).__init__(timeout=timeout)
        self.endpoint = endpoint
        self.auth_token = token
        self.auth_url = auth_url
        self.auth_tenant_id = auth_tenant_id
        self.username = username
        self.password = password
        self.tenant_name = tenant_name
        self.tenant_id = tenant_id
        self.region_name = region_name
        self.force_exception_to_status_code = True
        self.disable_ssl_certificate_validation = insecure
        if self.endpoint is None:
            self.authenticate()

    def _http_request(self, url, method, **kwargs):
        """ Send an http request with the specified characteristics.
        """

        kwargs['headers'] = copy.deepcopy(kwargs.get('headers', {}))
        kwargs['headers'].setdefault('User-Agent', self.USER_AGENT)
        if self.auth_token:
            kwargs['headers'].setdefault('X-Auth-Token', self.auth_token)

        resp, body = super(HTTPClient, self).request(url, method, **kwargs)

        if logger.isEnabledFor(logging.DEBUG):
            utils.http_log(logger, (url, method,), kwargs, resp, body)

        if resp.status in (301, 302, 305):
            return self._http_request(resp['location'], method, **kwargs)

        return resp, body

    def _json_request(self, method, url, **kwargs):
        """ Wrapper around _http_request to handle setting headers,
            JSON enconding/decoding and error handling.
        """

        kwargs.setdefault('headers', {})
        kwargs['headers'].setdefault('Content-Type', 'application/json')

        if 'body' in kwargs and kwargs['body'] is not None:
            kwargs['body'] = json.dumps(kwargs['body'])

        resp, body = self._http_request(url, method, **kwargs)

        if body:
            try:
                body = json.loads(body)
            except ValueError:
                logger.debug("Could not decode JSON from body: %s" % body)
        else:
            logger.debug("No body was returned.")
            body = None

        if 400 <= resp.status < 600:
            raise exceptions.from_response(resp, body)

        return resp, body

    def raw_request(self, method, url, **kwargs):
        url = self.endpoint + url

        kwargs.setdefault('headers', {})
        kwargs['headers'].setdefault('Content-Type',
                                     'application/octet-stream')

        resp, body = self._http_request(url, method, **kwargs)

        if 400 <= resp.status < 600:
            raise exceptions.from_response(resp, body)

        return resp, body

    def json_request(self, method, url, **kwargs):
        url = self.endpoint + url
        resp, body = self._json_request(method, url, **kwargs)
        return resp, body

    def authenticate(self):
        token_url = self.auth_url + "/tokens"
        body = {'auth': {'passwordCredentials': {'username': self.username,
                                                 'password': self.password}}}
        if self.tenant_id:
            body['auth']['tenantId'] = self.tenant_id
        elif self.tenant_name:
            body['auth']['tenantName'] = self.tenant_name

        tmp_follow_all_redirects = self.follow_all_redirects
        self.follow_all_redirects = True
        try:
            resp, body = self._json_request('POST', token_url, body=body)
        finally:
            self.follow_all_redirects = tmp_follow_all_redirects

        try:
            self.service_catalog = ServiceCatalog(body['access'])
            token = self.service_catalog.get_token()
            self.auth_token = token['id']
            self.auth_tenant_id = token['tenant_id']
        except KeyError:
            logger.exception("Parse service catalog failed.")
            raise exceptions.AuthorizationFailure()

        self.endpoint = self.service_catalog.url_for(attr='region',
                                    filter_value=self.region_name)
