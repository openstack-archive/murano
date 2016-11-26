# Copyright (c) 2016 Mirantis Inc.
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

from murano.common import auth_utils
from murano.dsl import dsl
from murano.dsl import helpers


@dsl.name('io.murano.User')
class User(object):
    @classmethod
    def get_current(cls):
        fields = auth_utils.get_user(helpers.get_execution_session().user_id)
        return cls._to_object(fields)

    @classmethod
    def get_environment_owner(cls):
        fields = auth_utils.get_user(
            helpers.get_execution_session().environment_owner_user_id)
        return cls._to_object(fields)

    @staticmethod
    def _to_object(fields):
        fields = dict(fields)
        for field in ('links', 'enabled', 'default_project_id'):
            fields.pop(field, None)
        obj_def = {
            'id': fields.pop('id'),
            'name': fields.pop('name'),
            'domain': fields.pop('domain_id', 'Default'),
            'email': fields.pop('email', None),
            'extra': fields
        }
        return dsl.new(obj_def)
