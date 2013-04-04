import unittest2
from mock import MagicMock

import portas.api.v1.router as router


def my_mock(link, controller, action, conditions):
    return [link, controller, action, conditions]


def func_mock():
    return True


class SanityUnitTests(unittest2.TestCase):

    def test_api(self):
        router.webservers = MagicMock(create_resource=func_mock)
        router.sessions = MagicMock(create_resource=func_mock)
        router.active_directories = MagicMock(create_resource=func_mock)
        router.environments = MagicMock(create_resource=func_mock)
        mapper = MagicMock(connect=my_mock)

        object = router.API(mapper)

        assert object._router is not None
