#    Copyright (c) 2015 Mirantis, Inc.
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

_FATAL_EXCEPTION_FORMAT_ERRORS = False

# Exceptions from openstack-common


class Error(Exception):
    def __init__(self, message=None):
        super(Error, self).__init__(message)


class OpenstackException(Exception):
    """Base Exception class.

    To correctly use this class, inherit from it and define
    a 'msg_fmt' property. That message will get printf'd
    with the keyword arguments provided to the constructor.
    """
    msg_fmt = "An unknown exception occurred"

    def __init__(self, **kwargs):
        try:
            self._error_string = self.msg_fmt % kwargs

        except Exception:
            if _FATAL_EXCEPTION_FORMAT_ERRORS:
                raise
            else:
                # at least get the io.murano message out if something happened
                self._error_string = self.msg_fmt

    def __str__(self):
        return self._error_string


class UnsupportedContentType(OpenstackException):
    msg_fmt = "Unsupported content type %(content_type)s"


class NotAcceptableContentType(OpenstackException):
    msg_fmt = ("Response with content type %(content_type)s "
               "expected but can not be provided")


class MalformedRequestBody(OpenstackException):
    msg_fmt = "Malformed message body: %(reason)s"

# Murano exceptions


class TimeoutException(Exception):
    pass


class PolicyViolationException(Exception):
    pass


class RouterInfoException(Exception):
    pass
