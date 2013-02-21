# Copyright 2010 Jacob Kaplan-Moss
# Copyright 2011 OpenStack LLC.
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

"""
Command-line interface to the OpenStack LBaaS API.
"""

import argparse
import httplib2
import os
import sys
import logging

from balancerclient.common import exceptions as exc
from balancerclient.common import utils
from balancerclient.v1 import shell as shell_v1


LOG = logging.getLogger(__name__)


class OpenStackBalancerShell(object):

    def get_base_parser(self):
        parser = argparse.ArgumentParser(
            prog='balancer',
            description=__doc__.strip(),
            epilog='See "balancer help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=OpenStackHelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h',
                            '--help',
                            action='store_true',
                            help=argparse.SUPPRESS)

        parser.add_argument('--debug',
                            default=False,
                            action='store_true',
                            help=argparse.SUPPRESS)

        parser.add_argument('--os_username',
                            metavar='<auth-user-name>',
                            default=utils.env('OS_USERNAME'),
                            help='Defaults to env[OS_USERNAME]')

        parser.add_argument('--os_password',
                            metavar='<auth-password>',
                            default=utils.env('OS_PASSWORD'),
                            help='Defaults to env[OS_PASSWORD]')

        parser.add_argument('--os_tenant_name',
                            metavar='<auth-tenant-name>',
                            default=utils.env('OS_TENANT_NAME'),
                            help='Defaults to env[OS_TENANT_NAME]')

        parser.add_argument('--os_tenant_id',
                            metavar='<tenant-id>',
                            default=utils.env('OS_TENANT_ID'),
                            help='Defaults to env[OS_TENANT_ID]')

        parser.add_argument('--os_auth_url',
                            metavar='<auth-url>',
                            default=utils.env('OS_AUTH_URL'),
                            help='Defaults to env[OS_AUTH_URL]')

        parser.add_argument('--os_region_name',
                            metavar='<region-name>',
                            default=utils.env('OS_REGION_NAME'),
                            help='Defaults to env[OS_REGION_NAME]')

        parser.add_argument('--os_balancer_api_version',
                            metavar='<balancer-api-version>',
                            default=utils.env('OS_BALANCER_API_VERSION',
                                        'KEYSTONE_VERSION'),
                            help='Defaults to env[OS_BALANCER_API_VERSION]'
                                 ' or 2.0')

        parser.add_argument('--token',
                            metavar='<service-token>',
                            default=utils.env('SERVICE_TOKEN'),
                            help='Defaults to env[SERVICE_TOKEN]')

        parser.add_argument('--endpoint',
                            metavar='<service-endpoint>',
                            default=utils.env('SERVICE_ENDPOINT'),
                            help='Defaults to env[SERVICE_ENDPOINT]')

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')

        try:
            actions_module = {
                '1': shell_v1,
            }[version]
        except KeyError:
            actions_module = shell_v1

        self._find_actions(subparsers, actions_module)
        self._find_actions(subparsers, self)

        return parser

    def _find_actions(self, subparsers, actions_module):
        for attr in (a for a in dir(actions_module) if a.startswith('do_')):
            # I prefer to be hypen-separated instead of underscores.
            command = attr[3:].replace('_', '-')
            callback = getattr(actions_module, attr)
            desc = callback.__doc__ or ''
            help = desc.strip().split('\n')[0]
            arguments = getattr(callback, 'arguments', [])

            subparser = subparsers.add_parser(
                command,
                help=help,
                description=desc,
                add_help=False,
                formatter_class=OpenStackHelpFormatter)
            subparser.add_argument('-h', '--help', action='help',
                                   help=argparse.SUPPRESS)
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def main(self, argv):
        # Parse args once to find version
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)

        # build available subcommands based on version
        api_version = options.os_balancer_api_version
        subcommand_parser = self.get_subcommand_parser(api_version)
        self.parser = subcommand_parser

        # Handle top-level --help/-h before attempting to parse
        # a command off the command line
        if not argv or options.help:
            self.do_help(options)
            return 0

        # Parse args again and call whatever callback was selected
        args = subcommand_parser.parse_args(argv)

        # Deal with global arguments
        if args.debug:
            httplib2.debuglevel = 1

        # Short-circuit and deal with help command right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0

        #FIXME(usrleon): Here should be restrict for project id same as
        # for username or apikey but for compatibility it is not.

        if not utils.isunauthenticated(args.func):
            # if the user hasn't provided any auth data
            if not (args.token or args.endpoint or args.os_username or
                    args.os_password or args.os_auth_url):
                raise exc.CommandError('Expecting authentication method via \n'
                                       '  either a service token, '
                                       '--token or env[SERVICE_TOKEN], \n'
                                       '  or credentials, '
                                       '--os_username or env[OS_USERNAME].')

            # if it looks like the user wants to provide a service token
            # but is missing something
            if args.token or args.endpoint and not (
                    args.token and args.endpoint):
                if not args.token:
                    raise exc.CommandError(
                        'Expecting a token provided via either --token or '
                        'env[SERVICE_TOKEN]')

                if not args.endpoint:
                    raise exc.CommandError(
                        'Expecting an endpoint provided via either --endpoint '
                        'or env[SERVICE_ENDPOINT]')

            # if it looks like the user wants to provide a credentials
            # but is missing something
            if ((args.os_username or args.os_password or args.os_auth_url)
                    and not (args.os_username and args.os_password and
                             args.os_auth_url)):
                if not args.os_username:
                    raise exc.CommandError(
                        'Expecting a username provided via either '
                        '--os_username or env[OS_USERNAME]')

                if not args.os_password:
                    raise exc.CommandError(
                        'Expecting a password provided via either '
                        '--os_password or env[OS_PASSWORD]')

                if not args.os_auth_url:
                    raise exc.CommandError(
                        'Expecting an auth URL via either --os_auth_url or '
                        'env[OS_AUTH_URL]')

        if utils.isunauthenticated(args.func):
            self.cs = shell_generic.CLIENT_CLASS(endpoint=args.os_auth_url)
        else:
            token = None
            endpoint = None
            if args.token and args.endpoint:
                token = args.token
                endpoint = args.endpoint
            api_version = options.os_balancer_api_version
            self.cs = self.get_api_class(api_version)(
                username=args.os_username,
                tenant_name=args.os_tenant_name,
                tenant_id=args.os_tenant_id,
                token=token,
                endpoint=endpoint,
                password=args.os_password,
                auth_url=args.os_auth_url,
                region_name=args.os_region_name)

        try:
            args.func(self.cs, args)
        except exc.Unauthorized:
            raise exc.CommandError("Invalid OpenStack LBaaS credentials.")
        except exc.AuthorizationFailure:
            raise exc.CommandError("Unable to authorize user")

    def get_api_class(self, version):
        try:
            return {
                "1": shell_v1.CLIENT_CLASS,
            }[version]
        except KeyError:
            return shell_v1.CLIENT_CLASS

    @utils.arg('command', metavar='<subcommand>', nargs='?',
                          help='Display help for <subcommand>')
    def do_help(self, args):
        """
        Display help about this program or one of its subcommands.
        """
        if getattr(args, 'command', None):
            if args.command in self.subcommands:
                self.subcommands[args.command].print_help()
            else:
                raise exc.CommandError("'%s' is not a valid subcommand" %
                                       args.command)
        else:
            self.parser.print_help()


# I'm picky about my shell help.
class OpenStackHelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(OpenStackHelpFormatter, self).start_section(heading)


def main():
    try:
        return OpenStackBalancerShell().main(sys.argv[1:])
    except Exception, err:
        LOG.exception("The operation executed with an error %r." % err)
        raise
