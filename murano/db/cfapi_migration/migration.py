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

import os

import alembic
from alembic import config as alembic_config
from alembic import migration as alembic_migration

from murano.db import session as db_session


def get_alembic_config():
    path = os.path.join(os.path.dirname(__file__), 'alembic.ini')

    config = alembic_config.Config(path)
    config.set_main_option('script_location',
                           'murano.db.cfapi_migration:alembic_migrations')
    return config


def version(engine=None):
    """Returns current database version."""
    engine = engine or db_session.get_engine()
    with engine.connect() as conn:
        context = alembic_migration.MigrationContext.configure(conn)
        return context.get_current_revision()


def upgrade(revision, config=None):
    """Used for upgrading database.

    :param version: Desired database version
    :type version: string
    """
    revision = revision or 'head'
    config = config or get_alembic_config()

    alembic.command.upgrade(config, revision or 'head')


def downgrade(revision, config=None):
    """Used for downgrading database.

    :param version: Desired database version7
    :type version: string
    """
    revision = revision or 'base'
    config = config or get_alembic_config()
    return alembic.command.downgrade(config, revision)


def stamp(revision, config=None):
    """Stamps database with provided revision.

    Don't run any migrations.

    :param revision: Should match one from repository or head - to stamp
                     database with most recent revision
    :type revision: string
    """
    config = config or get_alembic_config()
    return alembic.command.stamp(config, revision=revision)


def revision(message=None, autogenerate=False, config=None):
    """Creates template for migration.

    :param message: Text that will be used for migration title
    :type message: string
    :param autogenerate: If True - generates diff based on current database
                         state
    :type autogenerate: bool
    """
    config = config or get_alembic_config()
    return alembic.command.revision(config, message=message,
                                    autogenerate=autogenerate)
