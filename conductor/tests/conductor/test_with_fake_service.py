import unittest
from conductor.app import ConductorWorkflowService
from conductor.openstack.common import service

class TestMethodsAndClasses(unittest.TestCase):

    def test_init_service_class(self):
        launcher = service.ServiceLauncher()
        con = ConductorWorkflowService()
        launcher.launch_service(con)
        