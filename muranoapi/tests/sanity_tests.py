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

import unittest2
from mock import MagicMock

import muranoapi.api.v1.router as router


def my_mock(link, controller, action, conditions):
    return [link, controller, action, conditions]


def func_mock():
    return True


class SanityUnitTests(unittest2.TestCase):

    def test_api(self):
        router.webservers = MagicMock(create_resource=func_mock)
        router.aspNetApps = MagicMock(create_resource=func_mock)
        router.sessions = MagicMock(create_resource=func_mock)
        router.active_directories = MagicMock(create_resource=func_mock)
        router.environments = MagicMock(create_resource=func_mock)
        mapper = MagicMock(connect=my_mock)

        object = router.API(mapper)

        assert object._router is not None
