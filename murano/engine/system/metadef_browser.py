# Copyright (c) 2016 Mirantis Inc.
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

import glanceclient.v2.client as gclient
from oslo_config import cfg

from murano.common import auth_utils
from murano.dsl import dsl
from murano.dsl import helpers
from murano.dsl import session_local_storage


CONF = cfg.CONF


@dsl.name('io.murano.system.MetadefBrowser')
class MetadefBrowser(object):
    def __init__(self, this, region_name=None, cache=True):
        session = helpers.get_execution_session()
        self._project_id = session.project_id
        self._region = this.find_owner('io.murano.CloudRegion')
        self._region_name = region_name
        self._cache = cache
        self._namespaces = {}
        self._objects = {}

    @staticmethod
    @session_local_storage.execution_session_memoize
    def _get_client(region_name):
        return gclient.Client(**auth_utils.get_session_client_parameters(
            service_type='image', region=region_name, conf='glance'
        ))

    @property
    def _client(self):
        region = self._region_name or (
            None if self._region is None else self._region['name'])
        return self._get_client(region)

    def get_namespaces(self, resource_type):
        if not self._cache or resource_type not in self._namespaces:
            nss = list(self._client.metadefs_namespace.list(
                resource_type=resource_type))
            self._namespaces[resource_type] = nss
            return nss
        else:
            return self._namespaces[resource_type]

    def get_objects(self, namespace):
        if not self._cache or namespace not in self._objects:
            objects = list(self._client.metadefs_object.list(
                namespace=namespace))
            self._objects[namespace] = objects
            return objects
        else:
            return self._objects[namespace]
