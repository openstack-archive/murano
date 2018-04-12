# Copyright 2011 OpenStack Foundation
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

from keystoneauth1 import loading as ks_loading
from oslo_config import cfg
from oslo_log import log as logging
from oslo_middleware import cors

from murano.common.i18n import _
from murano import version

paste_deploy_opts = [
    cfg.StrOpt('flavor', help='Paste flavor'),
    cfg.StrOpt('config_file', help='Path to Paste config file'),
]

bind_opts = [
    cfg.HostAddressOpt('bind-host', default='0.0.0.0',
                       help='Address to bind the Murano API server to.'),
    cfg.PortOpt('bind-port',
                default=8082,
                help='Port the bind the Murano API server to.'),
]

rabbit_opts = [
    cfg.HostAddressOpt('host', default='localhost',
                       help='The RabbitMQ broker address which used for '
                            'communication with Murano guest agents.'),

    cfg.PortOpt('port',
                default=5672,
                help='The RabbitMQ broker port.'),

    cfg.StrOpt('login', default='guest',
               help='The RabbitMQ login.'),

    cfg.StrOpt('password', default='guest', secret=True,
               help='The RabbitMQ password.'),

    cfg.StrOpt('virtual_host', default='/',
               help='The RabbitMQ virtual host.'),

    cfg.BoolOpt('ssl', default=False,
                help='Boolean flag to enable SSL communication through the '
                'RabbitMQ broker between murano-engine and guest agents.'),

    cfg.StrOpt('ssl_version',
               default='',
               help='SSL version to use (valid only if SSL enabled). '
                    'Valid values are TLSv1 and SSLv23. SSLv2, SSLv3, '
                    'TLSv1_1, and TLSv1_2 may be available on some '
                    'distributions.'),

    cfg.StrOpt('ca_certs', default='',
               help='SSL cert file (valid only if SSL enabled).'),

    cfg.BoolOpt('insecure', default=False,
                help='This option explicitly allows Murano to perform '
                     '"insecure" SSL connections to RabbitMQ'),
]

heat_opts = [
    cfg.StrOpt('url', help='Optional heat endpoint override'),

    cfg.StrOpt('endpoint_type', default='publicURL',
               help='Heat endpoint type.'),

    cfg.ListOpt('stack_tags', default=['murano'],
                help='List of tags to be assigned to heat stacks created '
                     'during environment deployment.')
]

mistral_opts = [
    cfg.StrOpt('url', help='Optional mistral endpoint override'),

    cfg.StrOpt('endpoint_type', default='publicURL',
               help='Mistral endpoint type.'),

    cfg.StrOpt('service_type', default='workflowv2',
               help='Mistral service type.')
]

neutron_opts = [
    cfg.StrOpt('url', help='Optional neutron endpoint override'),

    cfg.StrOpt('endpoint_type', default='publicURL',
               help='Neutron endpoint type.')
]

murano_opts = [
    cfg.StrOpt('url', help='Optional murano url in format '
                           'like http://0.0.0.0:8082 used by Murano engine'),

    cfg.StrOpt('endpoint_type', default='publicURL',
               help='Murano endpoint type used by Murano engine.'),

    cfg.ListOpt('enabled_plugins',
                help="List of enabled Extension Plugins. "
                     "Remove or leave commented to enable all installed "
                     "plugins."),

    cfg.IntOpt('package_size_limit', default=5,
               help='Maximum application package size, Mb',
               deprecated_group='packages_opts'),

    cfg.IntOpt('limit_param_default', default=20,
               help='Default value for package pagination in API.',
               deprecated_group='packages_opts'),

    cfg.IntOpt('api_limit_max', default=100,
               help='Maximum number of packages to be returned in a single '
                    'pagination request',
               deprecated_group='packages_opts'),

    cfg.IntOpt('api_workers',
               help=_('Number of API workers')),

    cfg.IntOpt('dsl_iterators_limit', default=2000,
               help=_('Maximum number of elements that can be iterated per '
                      'object type.')),

]

networking_opts = [
    cfg.IntOpt('max_environments', default=250,
               help='Maximum number of environments that use a single router '
               'per tenant'),

    cfg.IntOpt('max_hosts', default=250,
               help='Maximum number of VMs per environment'),

    cfg.HostAddressOpt('env_ip_template', default='10.0.0.0',
                       help='Template IP address for generating environment '
                            'subnet cidrs'),

    cfg.ListOpt('default_dns', default=[],
                help='List of default DNS nameservers to be assigned to '
                     'created Networks'),

    cfg.StrOpt('external_network', default='ext-net',
               help='ID or name of the external network for routers '
                    'to connect to'),

    cfg.StrOpt('router_name', default='murano-default-router',
               help='Name of the router that going to be used in order to '
                    'join all networks created by Murano'),

    cfg.BoolOpt('create_router', default=True,
                help='This option will create a router when one with '
                     '"router_name" does not exist'),

    cfg.StrOpt('network_config_file', default='netconfig.yaml',
               help='If provided networking configuration will be taken '
                    'from this file'),

    cfg.StrOpt('driver', choices=['neutron', 'nova'],
               help='Network driver to use. Options are neutron or nova.'
                    'If not provided, the driver will be detected.'),
]

stats_opts = [
    cfg.IntOpt('period', default=5,
               help=_('Statistics collection interval in minutes.'
                      'Default value is 5 minutes.')),
    cfg.IntOpt('env_audit_period', default=60,
               help=_('Environment audit interval in minutes. '
                      'Default value is 60 minutes.')),
    cfg.BoolOpt('env_audit_enabled', default=True,
                help=_('Whether environment audit events enabled'))
]

engine_opts = [
    cfg.BoolOpt('disable_murano_agent', default=False,
                help=_('Disallow the use of murano-agent')),
    cfg.StrOpt('class_configs', default='/etc/murano/class-configs',
               help=_('Path to class configuration files')),
    cfg.BoolOpt('use_trusts', default=True,
                help=_("Create resources using trust token rather "
                       "than user's token")),
    cfg.BoolOpt('enable_model_policy_enforcer', default=False,
                help=_('Enable model policy enforcer using Congress')),
    cfg.IntOpt('agent_timeout', default=3600,
               help=_('Time for waiting for a response from murano agent '
                      'during the deployment')),
    cfg.IntOpt('engine_workers',
               deprecated_opts=[cfg.DeprecatedOpt('workers',
                                                  group='engine')],
               help=_('Number of engine workers')),

    cfg.ListOpt('load_packages_from', default=[],
                help=_('List of directories to load local packages from. '
                       'If not provided, packages will be loaded only API'),
                deprecated_group='packages_opts'),

    cfg.StrOpt('packages_cache',
               help='Location (directory) for Murano package cache.',
               deprecated_group='packages_opts'),

    cfg.BoolOpt('enable_packages_cache', default=True,
                help=_('Enables murano-engine to persist on disk '
                       'packages downloaded during deployments. '
                       'The packages would be re-used for consequent '
                       'deployments.'),
                deprecated_group='packages_opts'),

    cfg.StrOpt('packages_service', default='murano',
               help=_('The service to store murano packages: murano (stands '
                      'for legacy behavior using murano-api) or glance '
                      '(stands for glance-glare artifact service)'),
               deprecated_group='packages_opts'),

    cfg.StrOpt('signing_key', default='~/.ssh/id_rsa',
               help=_('Path to RSA key for agent message signing')),

    cfg.StrOpt('agent_source', default='murano-agent',
               help=_('pip URL/package spec for murano-agent')),
]

# TODO(sjmc7): move into engine opts?
metadata_dir = [
    cfg.StrOpt('metadata-dir', default='./meta',
               help='Metadata dir')
]

glare_opts = [
    cfg.StrOpt('url', help='Optional glare url in format '
                           'like http://0.0.0.0:9494 used by Glare API',
               deprecated_group='glance'),

    cfg.StrOpt('endpoint_type', default='publicURL',
               help='Glare endpoint type.',
               deprecated_group='glance')
]

glance_opts = [
    cfg.StrOpt('url', help='Optional glance endpoint override'),

    cfg.StrOpt('endpoint_type', default='publicURL',
               help='Glance endpoint type.')
]

file_server = [
    cfg.StrOpt('file_server', default='',
               help='Set a file server.')
]

home_region = cfg.StrOpt(
    'home_region',
    help="Default region name used to get services endpoints.")

# Unfortuntely we cannot use murano_auth.auth_url, since it
# is private to the actual authentication plugin used.
murano_auth_opts = [
    cfg.StrOpt('www_authenticate_uri',
               help='Identity API endpoint for authenticating with tokens.')]


CONF = cfg.CONF
CONF.register_opts(paste_deploy_opts, group='paste_deploy')
CONF.register_cli_opts(bind_opts)
CONF.register_opts(rabbit_opts, group='rabbitmq')
CONF.register_opts(heat_opts, group='heat')
CONF.register_opts(mistral_opts, group='mistral')
CONF.register_opts(neutron_opts, group='neutron')
CONF.register_opts(murano_opts, group='murano')
CONF.register_opts(engine_opts, group='engine')
CONF.register_opts(file_server)
CONF.register_opt(home_region)
CONF.register_cli_opts(metadata_dir)
CONF.register_opts(stats_opts, group='stats')
CONF.register_opts(networking_opts, group='networking')
CONF.register_opts(glare_opts, group='glare')
CONF.register_opts(glance_opts, group='glance')
CONF.register_opts(murano_auth_opts, group='murano_auth')
ks_loading.register_auth_conf_options(CONF, group='murano_auth')


for group in ('heat', 'mistral', 'neutron', 'glance', 'glare',
              'murano', 'murano_auth'):
    ks_loading.register_session_conf_options(
        CONF,
        group=group,
        deprecated_opts={
            'cafile':   [cfg.DeprecatedOpt('cacert', group),
                         cfg.DeprecatedOpt('ca_file', group)],
            'certfile': [cfg.DeprecatedOpt('cert_file', group)],
            'keyfile':  [cfg.DeprecatedOpt('key_file', group)]

        })


def parse_args(args=None, usage=None, default_config_files=None):
    logging.register_options(CONF)
    CONF(args=args,
         project='murano',
         version=version.version_string,
         usage=usage,
         default_config_files=default_config_files)


def set_middleware_defaults():
    """Update default configuration options for oslo.middleware."""

    cors.set_defaults(
        allow_headers=['X-Auth-Token',
                       'X-Openstack-Request-Id',
                       'X-Configuration-Session',
                       'X-Roles',
                       'X-User-Id',
                       'X-Tenant-Id'],
        expose_headers=['X-Auth-Token',
                        'X-Openstack-Request-Id',
                        'X-Configuration-Session',
                        'X-Roles',
                        'X-User-Id',
                        'X-Tenant-Id'],
        allow_methods=['GET',
                       'PUT',
                       'POST',
                       'DELETE',
                       'PATCH']
    )
