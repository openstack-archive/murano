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

import time

from oslo_log import log as logging

from murano.api import v1
from murano.common import wsgi
from murano.db.services import stats

LOG = logging.getLogger(__name__)


class RequestStatisticsCollection(object):
    request_count = 0
    error_count = 0
    average_time = 0.0

    requests_per_tenant = {}
    errors_per_tenant = {}

    def add_api_request(self, tenant, ex_time):
        self.average_time = (self.average_time * self.request_count +
                             ex_time) / (self.request_count + 1)
        if tenant:
            tenant_count = self.requests_per_tenant.get(tenant, 0)
            tenant_count += 1
            self.requests_per_tenant[tenant] = tenant_count

    def add_api_error(self, tenant, ex_time):
        self.average_time = (self.average_time * self.request_count +
                             ex_time) / (self.request_count + 1)
        if tenant:
            tenant_count = self.errors_per_tenant.get(tenant, 0)
            tenant_count += 1
            self.errors_per_tenant[tenant] = tenant_count


def stats_count(api, method):
    def wrapper(func):
        def wrap(*args, **kwargs):
            try:
                ts = time.time()
                result = func(*args, **kwargs)
                te = time.time()
                tenant = args[1].context.tenant
                update_count(api, method, te - ts,
                             tenant)
                return result
            except Exception:
                te = time.time()
                tenant = args[1].context.tenant
                LOG.exception('API {api} method {method} raised an '
                              'exception'.format(api=api, method=method))
                update_error_count(api, method, te - te, tenant)
                raise
        return wrap

    return wrapper


def update_count(api, method, ex_time, tenant=None):
    LOG.debug("Updating count stats for {api}, {method} on object {object}"
              .format(api=api, method=method, object=v1.stats))
    v1.stats.add_api_request(tenant, ex_time)
    v1.stats.request_count += 1


def update_error_count(api, method, ex_time, tenant=None):
    LOG.debug("Updating count stats for {api}, {method} on object "
              "{object}".format(api=api, method=method, object=v1.stats))
    v1.stats.add_api_error(tenant, ex_time)
    v1.stats.error_count += 1
    v1.stats.request_count += 1


def init_stats():
    if not v1.stats:
        v1.stats = RequestStatisticsCollection()


class Controller(object):
    def get(self, request):
        model = stats.Statistics()
        entries = model.get_all()
        ent_list = []
        for entry in entries:
            ent_list.append(entry.to_dict())
        return ent_list


def create_resource():
    return wsgi.Resource(Controller())
