import unittest
import mock


from windc.api.v1.router import API 


class TestBaseDriver(unittest.TestCase):
    def setUp(self):
        super(TestBaseDriver, self).setUp()
        self.conf = mock.Mock()

    def testAPI(self):
	api = API(None)
