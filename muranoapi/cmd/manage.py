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

"""
  CLI interface for murano management.
"""

import sys

from oslo.config import cfg

import muranoapi
from muranoapi.db import session as db_session
from muranoapi.openstack.common import log


CONF = cfg.CONF


def do_db_sync():
    """
    Place a database under migration control and upgrade,
    creating first if necessary.
    """
    db_session.db_sync()


def add_command_parsers(subparsers):
    parser = subparsers.add_parser('db_sync')
    parser.set_defaults(func=do_db_sync)
    parser.add_argument('version', nargs='?')
    parser.add_argument('current_version', nargs='?')

command_opt = cfg.SubCommandOpt('command',
                                title='Commands',
                                help='Show available commands.',
                                handler=add_command_parsers)


def main():
    CONF.register_cli_opt(command_opt)
    try:
        default_config_files = cfg.find_config_files('murano-api', 'murano')
        CONF(sys.argv[1:], project='murano-api', prog='murano-manage',
             version=muranoapi.__version__,
             default_config_files=default_config_files)
        log.setup("murano-api")
    except RuntimeError as e:
        sys.exit("ERROR: %s" % e)

    try:
        CONF.command.func()
    except Exception as e:
        sys.exit("ERROR: %s" % e)
