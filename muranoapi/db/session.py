# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
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
"""Session management functions."""

import os
import logging

from migrate.versioning import api as versioning_api
from migrate import exceptions as versioning_exceptions
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import DisconnectionError

from muranoapi.common.config import CONF as conf

from muranoapi.db import migrate_repo


MAKER = None
ENGINE = None


class MySQLPingListener(object):
    """
    Ensures that MySQL connections checked out of the
    pool are alive.

    Borrowed from:
    http://groups.google.com/group/sqlalchemy/msg/a4ce563d802c929f

    Error codes caught:
    * 2006 MySQL server has gone away
    * 2013 Lost connection to MySQL server during query
    * 2014 Commands out of sync; you can't run this command now
    * 2045 Can't open shared memory; no answer from server (%lu)
    * 2055 Lost connection to MySQL server at '%s', system error: %d

    from http://dev.mysql.com/doc/refman/5.6/ru_RU/error-messages-client.html
    """

    def checkout(self, dbapi_con, con_record, con_proxy):
        try:
            dbapi_con.cursor().execute('select 1')
        except dbapi_con.OperationalError, ex:
            if ex.args[0] in (2006, 2013, 2014, 2045, 2055):
                logging.warn('Got mysql server has gone away: %s', ex)
                raise DisconnectionError("Database server went away")
            else:
                raise


def get_session(autocommit=True, expire_on_commit=False):
    """Return a SQLAlchemy session."""
    global MAKER

    if MAKER is None:
        MAKER = sessionmaker(autocommit=autocommit,
                             expire_on_commit=expire_on_commit)
    engine = get_engine()
    MAKER.configure(bind=engine)
    session = MAKER()
    return session


def get_engine():
    """Return a SQLAlchemy engine."""
    global ENGINE

    connection_url = make_url(conf.sql_connection)
    if ENGINE is None or not ENGINE.url == connection_url:
        engine_args = {'pool_recycle': 3600,
                       'echo': False,
                       'convert_unicode': True
                       }
        if 'sqlite' in connection_url.drivername:
            engine_args['poolclass'] = NullPool
        if 'mysql' in connection_url.drivername:
            engine_args['listeners'] = [MySQLPingListener()]
        ENGINE = create_engine(conf.sql_connection, **engine_args)

        sync()
    return ENGINE


def sync():
    repo_path = os.path.abspath(os.path.dirname(migrate_repo.__file__))
    try:
        versioning_api.upgrade(conf.sql_connection, repo_path)
    except versioning_exceptions.DatabaseNotControlledError:
        versioning_api.version_control(conf.sql_connection, repo_path)
        versioning_api.upgrade(conf.sql_connection, repo_path)
