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

from oslo_serialization import jsonutils
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def LargeBinary():
    return sa.LargeBinary().with_variant(mysql.LONGBLOB(), 'mysql')


class JsonBlob(sa.TypeDecorator):
    impl = sa.Text

    def process_bind_param(self, value, dialect):
        return jsonutils.dumps(value)

    def process_result_value(self, value, dialect):
        if value is not None:
            return jsonutils.loads(value)
        return None
