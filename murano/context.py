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

from oslo_context import context

from murano.common import policy


class RequestContext(context.RequestContext):
    """Class that stores context info about an API request.

    Stores creditentials of the user, that is accessing API
    as well as additional request information.
    """

    def __init__(self, session=None, service_catalog=None,
                 **kwargs):
        super(RequestContext, self).__init__(**kwargs)
        self.session = session
        self.service_catalog = service_catalog
        if self.is_admin is None:
            self.is_admin = policy.check_is_admin(self)
