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


class DCService(base.Resource):

    def __repr__(self):
        return "<Service(%s)>" % self._info


class DCServiceManager(base.Manager):
    resource_class = DCService

    def list(self, datacenter):
        return self._list("/datacenters/%s/services" % base.getid(datacenter),
                          'services')

    def create(self, datacenter, parameters):
        body = {'dc_count': 1,}
        body.update(parameters)
        return self._create("/datacenters/%s/services" % base.getid(datacenter),
                            body, 'service')

    def delete(self, datacenter, service):
        return self._delete("/datacenters/%s/services/%s" % \
                            (base.getid(datacenter),
                             base.getid(service)))

    def get(self, datacenter, service):
        return self._get("/datacenters/%s/services/%s" % \
                         (base.getid(datacenter),
                          base.getid(service)),
                         'service')
