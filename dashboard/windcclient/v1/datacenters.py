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

from windcclient.common import base


class DC(base.Resource):
    """Represent load balancer device instance."""

    def __repr__(self):
        return "<DC(%s)>" % self._info


class DCManager(base.Manager):
    resource_class = DC

    def list(self):
        return self._list('/datacenters', 'datacenters')

    def create(self, name, **extra):
        body = {'name': name, 'services': {}}
        body.update(extra)
        return self._create('/datacenters', body, 'datacenter')

    def delete(self, datacenter):
        return self._delete("/datacenters/%s" % base.getid(datacenter))

    def get(self, datacenter):
        return self._get("/datacenters/%s" % base.getid(datacenter),
                         'datacenter')
