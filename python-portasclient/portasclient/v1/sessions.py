# Copyright 2012 OpenMeter LLC.
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
import anyjson

from portasclient.common import base


class Session(base.Resource):
    def __repr__(self):
        return '<Session %s>' % self._info

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class Status(base.Resource):
    def __repr__(self):
        return '<Status %s>' % self._info

    def data(self, **kwargs):
        return self.manager.data(self, **kwargs)


class SessionManager(base.Manager):
    resource_class = Session

    def list(self, environment_id):
        return self._list('environments/{id}/sessions'.
                          format(id=environment_id), 'sessions')

    def get(self, environment_id, session_id):
        return self._get('environments/{id}/sessions/{session_id}'.
                         format(id=environment_id, session_id=session_id))

    def configure(self, environment_id):
        return self._create('environments/{id}/configure'.
                            format(id=environment_id), None)

    def deploy(self, environment_id, session_id):
        path = 'environments/{id}/sessions/{session_id}/deploy'
        self.api.json_request('POST',
                              path.format(id=environment_id,
                                          session_id=session_id))

    def reports(self, environment_id, session_id):
        path = 'environments/{id}/sessions/{session_id}/reports'
        resp, body = self.api.json_request('GET',
                                           path.format(id=environment_id,
                                                       session_id=session_id))

        data = body.get('reports', [])
        return [Status(self, res, loaded=True) for res in data if res]

    def delete(self, environment_id, session_id):
        return self._delete("environments/{id}/sessions/{session_id}".
                            format(id=environment_id, session_id=session_id))
