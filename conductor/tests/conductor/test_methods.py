import unittest
from conductor.app import ConductorWorkflowService
import conductor.rabbitmq as rabbitmq
from conductor.workflow import Workflow
import conductor.xml_code_engine as engine

class TestMethodsAndClasses(unittest.TestCase):

    def test_init_service_class(self):
        con = ConductorWorkflowService()

        con.start()
        con.stop()