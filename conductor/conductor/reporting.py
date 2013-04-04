# Copyright (c) 2013 Mirantis Inc.
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

import xml_code_engine
import rabbitmq


class Reporter(object):
    def __init__(self, rmqclient, task_id, environment_id):
        self._rmqclient = rmqclient
        self._task_id = task_id
        self._environment_id = environment_id
        rmqclient.declare('task-reports')

    def _report_func(self, id, entity, text, **kwargs):
        body = {
            'id': id,
            'entity': entity,
            'text': text,
            'environment_id': self._environment_id
        }

        msg = rabbitmq.Message()
        msg.body = body
        msg.id = self._task_id

        self._rmqclient.send(
            message=msg,
            key='task-reports')


def _report_func(context, id, entity, text, **kwargs):
    reporter = context['/reporter']
    return reporter._report_func(id, entity, text, **kwargs)

xml_code_engine.XmlCodeEngine.register_function(_report_func, "report")
