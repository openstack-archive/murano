# Copyright 2012 OpenMeter LLC.
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

from portasclient.common import base


class Environment(base.Resource):
    def __repr__(self):
        return "<Meter %s>" % self._info

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class EnvironmentManager(base.Manager):
    resource_class = Environment

    def list(self):
        return self._list('environments', 'environments')