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

from glazierclient.common import base


class Environment(base.Resource):
    def __repr__(self):
        return "<Environment %s>" % self._info

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class EnvironmentManager(base.Manager):
    resource_class = Environment

    def list(self):
        return self._list('environments', 'environments')

    def create(self, name):
        return self._create('environments', {'name': name})

    def update(self, environment_id, name):
        return self._update('environments/{id}'.format(id=environment_id),
                            {'name': name})

    def delete(self, environment_id):
        return self._delete('environments/{id}'.format(id=environment_id))

    def get(self, environment_id):
        return self._get("environments/{id}".format(id=environment_id))
