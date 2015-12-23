# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

from murano import context
from murano.db import session


def dummy_context(user='test_username', tenant_id='test_tenant_id',
                  password='password', roles=None, user_id=None,
                  is_admin=False, request_id='dummy-request'):
    if roles is None:
        roles = []
    # NOTE(kzaitsev) passing non-False value by default to request_id, to
    # prevent generation during tests.
    return context.RequestContext.from_dict({
        'request_id': request_id,
        'tenant': tenant_id,
        'user': user,
        # 'roles': roles,  # Commented until policy check changes land
        'is_admin': is_admin,

    })


def save_models(*models):
    s = session.get_session()
    for m in models:
        m.save(s)
