#    Copyright (c) 2013 Mirantis, Inc.
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
Command-line interface to the Glazier Project.
"""

import argparse
import logging
import sys

import httplib2
from keystoneclient.v2_0 import client as ksclient
from glazierclient import client as glazierclient
from glazierclient.common import utils, exceptions


logger = logging.getLogger(__name__)


class GlazierShell(object):
    def get_base_parser(self):
        parser = argparse.ArgumentParser(
            prog='glazier',
            description=__doc__.strip(),
            epilog='See glazier help COMMAND" '
                   'for help on a specific command.',
            add_help=False,
            formatter_class=HelpFormatter,
        )

        # Global arguments
        parser.add_argument('-h', '--help',
                            action='store_true',
                            help=argparse.SUPPRESS,)

        parser.add_argument('-d', '--debug',
                            default=bool(utils.env('GLAZIERCLIENT_DEBUG')),
                            action='store_true',
                            help='Defaults to env[GLAZIERCLIENT_DEBUG]')

        parser.add_argument('-v', '--verbose',
                            default=False, action="store_true",
                            help="Print more verbose output")

        parser.add_argument('-k', '--insecure',
                            default=False,
                            action='store_true',
                            help="Explicitly allow glazierclient to perform "
                                 "\"insecure\" SSL (https) requests. "
                                 "The server's certificate will "
                                 "not be verified against any certificate "
                                 "authorities. This option should be used "
                                 "with caution.")

        parser.add_argument('--cert-file',
                            help='Path of certificate file to use in SSL '
                                 'connection. This file can optionally be '
                                 'prepended with the private key.')

        parser.add_argument('--key-file',
                            help='Path of client key to use in SSL connection.'
                                 ' This option is not necessary if your '
                                 'key is prepended to your cert file.')

        parser.add_argument('--ca-file',
                            help='Path of CA SSL certificate(s) used to verify'
                                 ' the remote server certificate. Without '
                                 'this option glance looks for the default '
                                 'system CA certificates.')

        parser.add_argument('--timeout',
                            default=600,
                            help='Number of seconds to wait for a response')

        parser.add_argument('--os-username',
                            default=utils.env('OS_USERNAME'),
                            help='Defaults to env[OS_USERNAME]')

        parser.add_argument('--os-password',
                            default=utils.env('OS_PASSWORD'),
                            help='Defaults to env[OS_PASSWORD]')

        parser.add_argument('--os-tenant-id',
                            default=utils.env('OS_TENANT_ID'),
                            help='Defaults to env[OS_TENANT_ID]')

        parser.add_argument('--os-tenant-name',
                            default=utils.env('OS_TENANT_NAME'),
                            help='Defaults to env[OS_TENANT_NAME]')

        parser.add_argument('--os-auth-url',
                            default=utils.env('OS_AUTH_URL'),
                            help='Defaults to env[OS_AUTH_URL]')

        parser.add_argument('--os-region-name',
                            default=utils.env('OS_REGION_NAME'),
                            help='Defaults to env[OS_REGION_NAME]')

        parser.add_argument('--os-auth-token',
                            default=utils.env('OS_AUTH_TOKEN'),
                            help='Defaults to env[OS_AUTH_TOKEN]')

        parser.add_argument('--glazier-url',
                            default=utils.env('GLAZIER_URL'),
                            help='Defaults to env[GLAZIER_URL]')

        parser.add_argument('--glazier-api-version',
                            default=utils.env(
                                'GLAZIER_API_VERSION', default='1'),
                            help='Defaults to env[GLAZIER_API_VERSION] '
                                 'or 1')

        parser.add_argument('--os-service-type',
                            default=utils.env('OS_SERVICE_TYPE'),
                            help='Defaults to env[OS_SERVICE_TYPE]')

        parser.add_argument('--os-endpoint-type',
                            default=utils.env('OS_ENDPOINT_TYPE'),
                            help='Defaults to env[OS_ENDPOINT_TYPE]')

        return parser

    def get_subcommand_parser(self, version):
        parser = self.get_base_parser()

        self.subcommands = {}
        subparsers = parser.add_subparsers(metavar='<subcommand>')
        submodule = utils.import_versioned_module(version, 'shell')
        self._find_actions(subparsers, submodule)
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

            subparser = subparsers.add_parser(command, help=help,
                                              description=desc,
                                              add_help=False,
                                              formatter_class=HelpFormatter)
            subparser.add_argument('-h', '--help', action='help',
                                   help=argparse.SUPPRESS)
            self.subcommands[command] = subparser
            for (args, kwargs) in arguments:
                subparser.add_argument(*args, **kwargs)
            subparser.set_defaults(func=callback)

    def _get_ksclient(self, **kwargs):
        """Get an endpoint and auth token from Keystone.

        :param username: name of user
        :param password: user's password
        :param tenant_id: unique identifier of tenant
        :param tenant_name: name of tenant
        :param auth_url: endpoint to authenticate against
        """
        return ksclient.Client(username=kwargs.get('username'),
                               password=kwargs.get('password'),
                               tenant_id=kwargs.get('tenant_id'),
                               tenant_name=kwargs.get('tenant_name'),
                               auth_url=kwargs.get('auth_url'),
                               insecure=kwargs.get('insecure'))

    def _get_endpoint(self, client, **kwargs):
        """Get an endpoint using the provided keystone client."""
        return client.service_catalog.url_for(
            service_type=kwargs.get('service_type') or 'metering',
            endpoint_type=kwargs.get('endpoint_type') or 'publicURL')

    def _setup_debugging(self, debug):
        if debug:
            logging.basicConfig(
                format="%(levelname)s (%(module)s:%(lineno)d) %(message)s",
                level=logging.DEBUG)

            httplib2.debuglevel = 1
        else:
            logging.basicConfig(
                format="%(levelname)s %(message)s",
                level=logging.INFO)

    def main(self, argv):
        # Parse args once to find version
        parser = self.get_base_parser()
        (options, args) = parser.parse_known_args(argv)
        self._setup_debugging(options.debug)

        # build available subcommands based on version
        api_version = options.glazier_api_version
        subcommand_parser = self.get_subcommand_parser(api_version)
        self.parser = subcommand_parser

        # Handle top-level --help/-h before attempting to parse
        # a command off the command line
        if options.help or not argv:
            self.do_help(options)
            return 0

        # Parse args again and call whatever callback was selected
        args = subcommand_parser.parse_args(argv)

        # Short-circuit and deal with help command right away.
        if args.func == self.do_help:
            self.do_help(args)
            return 0

        if args.os_auth_token and args.glazier_url:
            token = args.os_auth_token
            endpoint = args.glazier_url
        else:
            if not args.os_username:
                raise exceptions.CommandError("You must provide a username "
                                              "via either --os-username "
                                              "or via env[OS_USERNAME]")

            if not args.os_password:
                raise exceptions.CommandError("You must provide a password "
                                              "via either --os-password "
                                              "or via env[OS_PASSWORD]")

            if not (args.os_tenant_id or args.os_tenant_name):
                raise exceptions.CommandError("You must provide a tenant_id "
                                              "via either --os-tenant-id "
                                              "or via env[OS_TENANT_ID]")

            if not args.os_auth_url:
                raise exceptions.CommandError("You must provide an auth url "
                                              "via either --os-auth-url or "
                                              "via env[OS_AUTH_URL]")
            kwargs = {
                'username': args.os_username,
                'password': args.os_password,
                'tenant_id': args.os_tenant_id,
                'tenant_name': args.os_tenant_name,
                'auth_url': args.os_auth_url,
                'service_type': args.os_service_type,
                'endpoint_type': args.os_endpoint_type,
                'insecure': args.insecure
            }
            _ksclient = self._get_ksclient(**kwargs)
            token = args.os_auth_token or _ksclient.auth_token

            url = args.glazier_url
            endpoint = url or self._get_endpoint(_ksclient, **kwargs)

        kwargs = {
            'token': token,
            'insecure': args.insecure,
            'timeout': args.timeout,
            'ca_file': args.ca_file,
            'cert_file': args.cert_file,
            'key_file': args.key_file,
        }

        client = glazierclient.Client(api_version, endpoint, **kwargs)

        try:
            args.func(client, args)
        except exceptions.Unauthorized:
            msg = "Invalid OpenStack Identity credentials."
            raise exceptions.CommandError(msg)

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
                msg = "'%s' is not a valid subcommand"
                raise exceptions.CommandError(msg % args.command)
        else:
            self.parser.print_help()


class HelpFormatter(argparse.HelpFormatter):
    def start_section(self, heading):
        # Title-case the headings
        heading = '%s%s' % (heading[0].upper(), heading[1:])
        super(HelpFormatter, self).start_section(heading)


def main():
    try:
        GlazierShell().main(sys.argv[1:])

    except Exception, e:
        print >> sys.stderr, e
        sys.exit(1)


if __name__ == "__main__":
    main()
