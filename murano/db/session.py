#    Copyright (c) 2014 Mirantis, Inc.
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

"""Session management functions."""

from murano.common import config
from murano.openstack.common.db.sqlalchemy import session as db_session
from murano.openstack.common import log as logging

LOG = logging.getLogger(__name__)
CONF = config.CONF
_FACADE = None


def _create_facade_lazily():
    global _FACADE

    if _FACADE is None:
        _FACADE = db_session.EngineFacade(
            CONF.database.connection, sqlite_fk=True,
            **dict(CONF.database.iteritems())
        )
    return _FACADE


def get_session(autocommit=True, expire_on_commit=False):
    s = _create_facade_lazily().get_session(autocommit=autocommit,
                                            expire_on_commit=expire_on_commit)
    return s


def get_engine():
    return _create_facade_lazily().get_engine()
