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

from oslo_config import cfg
from oslo_db import options

from murano.db.cfapi_migration import migration

CONF = cfg.CONF
options.set_defaults(CONF)


class ApiDBCommand(object):

    def upgrade(self, config):
        migration.upgrade(CONF.command.revision, config=config)

    def downgrade(self, config):
        migration.downgrade(CONF.command.revision, config=config)

    def revision(self, config):
        migration.revision(CONF.command.message,
                           CONF.command.autogenerate,
                           config=config)

    def stamp(self, config):
        migration.stamp(CONF.command.revision, config=config)

    def version(self, config):
        print(migration.version())


def add_command_parsers(subparsers):
    command_object = ApiDBCommand()

    parser = subparsers.add_parser('upgrade')
    parser.set_defaults(func=command_object.upgrade)
    parser.add_argument('--revision', nargs='?')

    parser = subparsers.add_parser('downgrade')
    parser.set_defaults(func=command_object.downgrade)
    parser.add_argument('--revision', nargs='?')

    parser = subparsers.add_parser('stamp')
    parser.add_argument('--revision', nargs='?')
    parser.set_defaults(func=command_object.stamp)

    parser = subparsers.add_parser('revision')
    parser.add_argument('-m', '--message')
    parser.add_argument('--autogenerate', action='store_true')
    parser.set_defaults(func=command_object.revision)

    parser = subparsers.add_parser('version')
    parser.set_defaults(func=command_object.version)


command_opt = cfg.SubCommandOpt('command',
                                title='Command',
                                help='Available commands',
                                handler=add_command_parsers)

CONF.register_cli_opt(command_opt)


def main():
    config = migration.get_alembic_config()
    # attach the Murano conf to the Alembic conf
    config.murano_config = CONF

    CONF(project='murano')
    CONF.command.func(config)
