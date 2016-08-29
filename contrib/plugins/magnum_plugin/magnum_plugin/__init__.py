# Copyright (c) 2016 Intel, Inc.
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

import cfg
import time

from magnumclient import client
from murano.common import auth_utils
from murano.dsl import session_local_storage
from oslo_config import cfg as config

try:
    from magnumclient.common.apiclient import exceptions
except ImportError:
    # NOTE (hongbin): For magnumclient versions before 2.0.0.
    from magnumclient.openstack.common.apiclient import exceptions

CONF = config.CONF


class MagnumClient(object):
    def __init__(self, this, region_name=None):
        self._region_name = region_name
        self._owner = this.find_owner('io.murano.Environment')

    @property
    def _client(self):
        region = self._region_name or (
            None if self._owner is None else self._owner['region'])
        return self._create_magnum_client(region)

    @classmethod
    def init_plugin(cls):
        cls.CONF = cfg.init_config(CONF)

    def _wait_on_status(self, bays, bay_id, wait_status, finish_status):
        while True:
            # sleep 1s to wait bay status changes, this will be useful for
            # the first time we wait for the status, to avoid another 30s
            time.sleep(1)
            status = bays.get(bay_id).status
            if status in wait_status:
                time.sleep(30)
            elif status in finish_status:
                break
            else:
                raise RuntimeError("Unexpected Status: {}".format(status))

    @staticmethod
    @session_local_storage.execution_session_memoize
    def _create_magnum_client(region):
        session = auth_utils.get_token_client_session(conf=CONF)
        params = auth_utils.get_session_client_parameters(
            service_type='container-infra', region=region, conf=CONF,
            session=session)
        return client.Client(**params)

    def create_baymodel(self, args):
        baymodel = self._client.baymodels.create(**args)
        return baymodel.uuid

    def delete_baymodel(self, baymodel_id):
        self._client.baymodels.delete(baymodel_id)

    def get_bay_status(self, bay_id):
        bays = self._client.bays
        bay = bays.get(bay_id)
        return bay.status

    def create_bay(self, args):
        bays = self._client.bays
        bay = bays.create(**args)
        self._wait_on_status(bays, bay.uuid, [None, "CREATE_IN_PROGRESS"],
                             ["CREATE_COMPLETE", "CREATE_FAILED"])
        return bay.uuid

    def delete_bay(self, bay_id):
        bays = self._client.bays
        bays.delete(bay_id)
        try:
            self._wait_on_status(bays, bay_id, ["CREATE_COMPLETE",
                                 "DELETE_IN_PROGRESS", "CREATE_FAILED"],
                                 ["DELETE_COMPLETE"])
        except exceptions.NotFound:
            pass
