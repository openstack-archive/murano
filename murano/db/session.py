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
import threading

from oslo.db import options
from oslo.db.sqlalchemy import session as db_session

from murano.common import config
from murano.openstack.common import log as logging

LOG = logging.getLogger(__name__)
CONF = config.CONF

options.set_defaults(CONF)

_FACADE = None
_LOCK = threading.Lock()


def _create_facade_lazily():
    global _LOCK, _FACADE

    if _FACADE is None:
        with _LOCK:
            if _FACADE is None:
                _FACADE = db_session.EngineFacade.from_config(CONF,
                                                              sqlite_fk=True)
    return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)
