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

from murano.common import policy


class RequestContext(object):
    """Stores information about the security context under which the user
    accesses the system, as well as additional request information.

    TODO: (sjmc7) - extend openstack.common.context
    """

    def __init__(self, auth_token=None, user=None,
                 tenant=None, session=None, is_admin=None,
                 roles=None):
        self.auth_token = auth_token
        self.user = user
        self.tenant = tenant
        self.session = session
        self.is_admin = is_admin
        self.roles = roles or []

        if self.is_admin is None:
            self.is_admin = policy.check_is_admin(self)

    def to_dict(self):
        return {
            'user': self.user,
            'tenant': self.tenant,
            'auth_token': self.auth_token,
            'session': self.session,
            'roles': self.roles,
            'is_admin': self.is_admin
        }

    @classmethod
    def from_dict(cls, values):
        return cls(**values)
