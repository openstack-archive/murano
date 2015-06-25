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

import logging
import sys

from murano.openstack.common import log
from murano.tests.unit import base


class SysLogHandlersTestCase(base.MuranoTestCase):
    """Test for standard and RFC compliant Syslog handlers."""

    def setUp(self):
        super(SysLogHandlersTestCase, self).setUp()

        if sys.platform != 'linux2':
            self.skip("SKIP: This test work on Linux platform only.")

        self.facility = logging.handlers.SysLogHandler.LOG_USER
        self.rfclogger = log.RFCSysLogHandler(address='/dev/log',
                                              facility=self.facility)
        self.rfclogger.binary_name = 'Foo_application'
        self.logger = logging.handlers.SysLogHandler(address='/dev/log',
                                                     facility=self.facility)
        self.logger.binary_name = 'Foo_application'

    def test_rfc_format(self):
        """Ensure syslog msg contains APP-NAME for RFC wrapped handler."""
        logrecord = logging.LogRecord('name', 'WARN', '/tmp', 1,
                                      'Message', None, None)
        expected = logging.LogRecord('name', 'WARN', '/tmp', 1,
                                     'Foo_application Message', None, None)
        self.assertEqual(self.rfclogger.format(logrecord),
                         expected.getMessage())

    def test_standard_format(self):
        """Ensure syslog msg isn't modified for standard handler."""
        logrecord = logging.LogRecord('name', 'WARN', '/tmp', 1,
                                      'Message', None, None)
        expected = logrecord
        self.assertEqual(self.logger.format(logrecord),
                         expected.getMessage())
