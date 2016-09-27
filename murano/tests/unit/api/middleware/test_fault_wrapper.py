# Copyright 2016 AT&T Corp
# All Rights Reserved.
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

import mock

from murano.api.middleware import fault
from murano.common import wsgi
from murano.packages import exceptions
from murano.tests.unit import base

from oslo_serialization import jsonutils

from webob import exc


class FaultWrapperTest(base.MuranoTestCase):
    @mock.patch('traceback.format_exc')
    def test_error_500(self, mock_trace):
        mock_trace.return_value = "test trace"
        fault_wrapper = fault.FaultWrapper(None)
        result = fault_wrapper._error(exc.HTTPInternalServerError())
        self.assertEqual(result['code'], 500)
        self.assertEqual(result['explanation'],
                         'The server has either erred or is incapable'
                         ' of performing the requested operation.')

    @mock.patch('traceback.format_exc')
    def test_error_value_error(self, mock_trace):
        mock_trace.return_value = "test trace"
        fault_wrapper = fault.FaultWrapper(None)
        exception = exceptions.PackageClassLoadError("test")
        exception.message = "Unable to load class 'test' from package"
        result = fault_wrapper._error(exception)
        self.assertEqual(result['code'], 400)
        self.assertEqual(result['error']['message'],
                         "Unable to load class 'test' from package")

    @mock.patch('traceback.format_exc')
    def test_fault_wrapper(self, mock_trace):
        mock_trace.return_value = "test trace"
        fault_wrapper = fault.FaultWrapper(None)
        exception_disguise = fault.HTTPExceptionDisguise(
            exc.HTTPInternalServerError())
        result = fault_wrapper._error(exception_disguise)
        self.assertEqual(result['code'], 500)
        self.assertEqual(result['explanation'],
                         'The server has either erred or is incapable'
                         ' of performing the requested operation.')

    def test_process_request(self):
        fault_wrapper = fault.FaultWrapper(None)
        environ = {
            'SERVER_NAME': 'server.test',
            'SERVER_PORT': '8082',
            'SERVER_PROTOCOL': 'http',
            'SCRIPT_NAME': '/',
            'PATH_INFO': '/asdf/asdf/asdf/asdf',
            'wsgi.url_scheme': 'http',
            'QUERY_STRING': '',
            'CONTENT_TYPE': 'application/json',
            'REQUEST_METHOD': 'HEAD'
        }
        req = wsgi.Request(environ)
        req.get_response = mock.MagicMock(side_effect=exc.
                                          HTTPInternalServerError())
        self.assertRaises(exc.HTTPInternalServerError,
                          fault_wrapper.process_request, req)

    @mock.patch('traceback.format_exc')
    def test_fault_call(self, mock_trace):
        mock_trace.return_value = "test trace"
        fault_wrapper = fault.FaultWrapper(None)
        exception = exceptions.PackageClassLoadError("test")
        exception.message = "Unable to load class 'test' from package"
        test_fault = fault.Fault(fault_wrapper._error(exception))
        environ = {
            'SERVER_NAME': 'server.test',
            'SERVER_PORT': '8082',
            'SERVER_PROTOCOL': 'http',
            'SCRIPT_NAME': '/',
            'PATH_INFO': '/',
            'wsgi.url_scheme': 'http',
            'QUERY_STRING': '',
            'CONTENT_TYPE': 'application/json',
            'REQUEST_METHOD': 'HEAD'
        }
        req = wsgi.Request(environ)
        response = jsonutils.loads(test_fault(req).body)
        self.assertEqual(response['code'], 400)
