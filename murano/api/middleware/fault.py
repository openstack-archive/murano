# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""A middleware that turns exceptions into parsable string. Inspired by
Cinder's faultwrapper
"""

import sys
import traceback

from oslo_config import cfg
import six
import webob

from murano.common import wsgi
from murano.packages import exceptions as pkg_exc


class HTTPExceptionDisguise(Exception):
    """Disguises HTTP exceptions

    Disguises HTTP exceptions so they can be handled by the webob fault
    application in the wsgi pipeline.
    """

    def __init__(self, exception):
        self.exc = exception
        self.tb = sys.exc_info()[2]


class Fault(object):

    def __init__(self, error):
        self.error = error

    @webob.dec.wsgify(RequestClass=wsgi.Request)
    def __call__(self, req):
        if req.content_type == 'application/xml':
            serializer = wsgi.XMLDictSerializer()
        else:
            serializer = wsgi.JSONDictSerializer()
        resp = webob.Response(request=req)
        default_webob_exc = webob.exc.HTTPInternalServerError()
        resp.status_code = self.error.get('code', default_webob_exc.code)
        serializer.default(resp, self.error)
        return resp


class FaultWrapper(wsgi.Middleware):
    """Replace error body with something the client can parse."""

    @classmethod
    def factory(cls, global_conf, **local_conf):
        def filter(app):
            return cls(app)
        return filter

    error_map = {
        'ValueError': webob.exc.HTTPBadRequest,
        'LookupError': webob.exc.HTTPNotFound,
        'PackageClassLoadError': webob.exc.HTTPBadRequest,
        'PackageUILoadError': webob.exc.HTTPBadRequest,
        'PackageLoadError': webob.exc.HTTPBadRequest,
        'PackageFormatError': webob.exc.HTTPBadRequest,
    }

    def _map_exception_to_error(self, class_exception):
        if class_exception == Exception:
            return webob.exc.HTTPInternalServerError

        if class_exception.__name__ not in self.error_map:
            return self._map_exception_to_error(class_exception.__base__)

        return self.error_map[class_exception.__name__]

    def _error(self, ex):

        trace = None
        webob_exc = None
        if isinstance(ex, HTTPExceptionDisguise):
            # An HTTP exception was disguised so it could make it here
            # let's remove the disguise and set the original HTTP exception
            if cfg.CONF.debug:
                trace = ''.join(traceback.format_tb(ex.tb))
            ex = ex.exc
            webob_exc = ex

        ex_type = ex.__class__.__name__

        full_message = six.text_type(ex)
        if full_message.find('\n') > -1:
            message, msg_trace = full_message.split('\n', 1)
        else:
            msg_trace = traceback.format_exc()
            message = full_message

        if isinstance(ex, pkg_exc.PackageException):
            message = ex.message

        if cfg.CONF.debug and not trace:
            trace = msg_trace

        if not webob_exc:
            webob_exc = self._map_exception_to_error(ex.__class__)

        error = {
            'code': webob_exc.code,
            'title': webob_exc.title,
            'explanation': webob_exc.explanation,
            'error': {
                'message': message,
                'type': ex_type,
                'traceback': trace,
            }
        }

        return error

    def process_request(self, req):
        try:
            return req.get_response(self.application)
        except Exception as exc:
            return req.get_response(Fault(self._error(exc)))
