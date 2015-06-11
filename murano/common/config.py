#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import logging
import logging.config
import logging.handlers
import os
import sys

from oslo.config import cfg
from paste import deploy

from murano.common.i18n import _
from murano import version

paste_deploy_opts = [
    cfg.StrOpt('flavor', help='Paste flavor'),
    cfg.StrOpt('config_file', help='Path to Paste config file'),
]

bind_opts = [
    cfg.StrOpt('bind-host', default='0.0.0.0',
               help='Address to bind the Murano API server to.'),
    cfg.IntOpt('bind-port', default=8082,
               help='Port the bind the Murano API server to.'),
]

rabbit_opts = [
    cfg.StrOpt('host', default='localhost',
               help='The RabbitMQ broker address which used for communication '
               'with Murano guest agents.'),

    cfg.IntOpt('port', default=5672,
               help='The RabbitMQ broker port.'),

    cfg.StrOpt('login', default='guest',
               help='The RabbitMQ login.'),

    cfg.StrOpt('password', default='guest',
               help='The RabbitMQ password.'),

    cfg.StrOpt('virtual_host', default='/',
               help='The RabbitMQ virtual host.'),

    cfg.BoolOpt('ssl', default=False,
                help='Boolean flag to enable SSL communication through the '
                'RabbitMQ broker between murano-engine and guest agents.'),
    cfg.StrOpt('ca_certs', default='',
               help='SSL cert file (valid only if SSL enabled).')
]

heat_opts = [
    cfg.BoolOpt('insecure', default=False,
                help='This option explicitly allows Murano to perform '
                '"insecure" SSL connections and transfers with Heat API.'),

    cfg.StrOpt('ca_file',
               help='(SSL) Tells Murano to use the specified certificate file '
               'to verify the peer running Heat API.'),

    cfg.StrOpt('cert_file',
               help='(SSL) Tells Murano to use the specified client '
               'certificate file when communicating with Heat.'),

    cfg.StrOpt('key_file', help='(SSL/SSH) Private key file name to '
                                'communicate with Heat API.'),

    cfg.StrOpt('endpoint_type', default='publicURL',
               help='Heat endpoint type.')
]

mistral_opts = [
    cfg.StrOpt('endpoint_type', default='publicURL',
               help='Mistral endpoint type.'),
    cfg.StrOpt('service_type', default='workflowv2',
               help='Mistral service type.')
]

neutron_opts = [
    cfg.BoolOpt('insecure', default=False,
                help='This option explicitly allows Murano to perform '
                '"insecure" SSL connections and transfers with Neutron API.'),

    cfg.StrOpt('ca_cert',
               help='(SSL) Tells Murano to use the specified client '
               'certificate file when communicating with Neutron.'),

    cfg.StrOpt('endpoint_type', default='publicURL',
               help='Neutron endpoint type.')
]

keystone_opts = [
    cfg.BoolOpt('insecure', default=False,
                help='This option explicitly allows Murano to perform '
                     '"insecure" SSL connections and transfers with '
                     'Keystone API running Kyestone API.'),

    cfg.StrOpt('ca_file',
               help='(SSL) Tells Murano to use the specified certificate file '
                    'to verify the peer when communicating with Keystone.'),

    cfg.StrOpt('cert_file',
               help='(SSL) Tells Murano to use the specified client '
                    'certificate file when communicating with Keystone.'),

    cfg.StrOpt('key_file', help='(SSL/SSH) Private key file name to '
                                'communicate with Keystone API')
]

murano_opts = [
    cfg.StrOpt('url', help='Optional murano url in format '
                           'like http://0.0.0.0:8082 used by Murano engine'),

    cfg.BoolOpt('insecure', default=False,
                help='This option explicitly allows Murano to perform '
                     '"insecure" SSL connections and transfers used by '
                     'Murano engine.'),

    cfg.StrOpt('cacert',
               help='(SSL) Tells Murano to use the specified client '
               'certificate file when communicating with Murano API '
               'used by Murano engine.'),

    cfg.StrOpt('cert_file',
               help='(SSL) Tells Murano to use the specified client '
                    'certificate file when communicating with Murano '
                    'used by Murano engine.'),

    cfg.StrOpt('key_file', help='(SSL/SSH) Private key file name '
                                'to communicate with Murano API used by '
                                'Murano engine.'),

    cfg.StrOpt('endpoint_type', default='publicURL',
               help='Murano endpoint type used by Murano engine.'),

    cfg.ListOpt('enabled_plugins', default=None,
                help="List of enabled Extension Plugins. "
                     "Remove or leave commented to enable all installed "
                     "plugins.")
]

networking_opts = [
    cfg.IntOpt('max_environments', default=20,
               help='Maximum number of environments that use a single router '
               'per tenant'),

    cfg.IntOpt('max_hosts', default=250,
               help='Maximum number of VMs per environment'),

    cfg.StrOpt('env_ip_template', default='10.0.0.0',
               help='Template IP address for generating environment '
               'subnet cidrs'),

    cfg.StrOpt('default_dns', default='8.8.8.8',
               help='Default DNS nameserver to be assigned to '
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
                    'from this file')
]
stats_opts = [
    cfg.IntOpt('period', default=5,
               help=_('Statistics collection interval in minutes.'
                      'Default value is 5 minutes.'))
]

engine_opts = [
    cfg.BoolOpt('disable_murano_agent', default=False,
                help=_('Disallow the use of murano-agent')),
    cfg.StrOpt('class_configs', default='/etc/murano/class-configs',
               help=_('Path to class configuration files')),
    cfg.BoolOpt('use_trusts', default=False,
                help=_("Create resources using trust token rather "
                       "than user's token")),
    cfg.BoolOpt('enable_model_policy_enforcer', default=False,
                help=_('Enable model policy enforcer using Congress')),
    cfg.IntOpt('agent_timeout', default=3600,
               help=_('Time for waiting for a response from murano agent'
                      'during the deployment'))
]

# TODO(sjmc7): move into engine opts?
metadata_dir = [
    cfg.StrOpt('metadata-dir', default='./meta',
               help='Metadata dir')
]

packages_opts = [
    cfg.StrOpt('packages_cache', default=None,
               help='Location (directory) for Murano package cache.'),

    cfg.IntOpt('package_size_limit', default=5,
               help='Maximum application package size, Mb'),

    cfg.IntOpt('limit_param_default', default=20,
               help='Default value for package pagination in API.'),

    cfg.IntOpt('api_limit_max', default=100,
               help='Maximum number of packages to be returned in a single '
                    'pagination request')
]

file_server = [
    cfg.StrOpt('file_server', default='')
]

CONF = cfg.CONF
CONF.register_opts(paste_deploy_opts, group='paste_deploy')
CONF.register_cli_opts(bind_opts)
CONF.register_opts(rabbit_opts, group='rabbitmq')
CONF.register_opts(heat_opts, group='heat')
CONF.register_opts(mistral_opts, group='mistral')
CONF.register_opts(neutron_opts, group='neutron')
CONF.register_opts(keystone_opts, group='keystone')
CONF.register_opts(murano_opts, group='murano')
CONF.register_opts(engine_opts, group='engine')
CONF.register_opts(file_server)
CONF.register_cli_opts(metadata_dir)
CONF.register_opts(packages_opts, group='packages_opts')
CONF.register_opts(stats_opts, group='stats')
CONF.register_opts(networking_opts, group='networking')


def parse_args(args=None, usage=None, default_config_files=None):
    CONF(args=args,
         project='murano',
         version=version.version_string,
         usage=usage,
         default_config_files=default_config_files)


def setup_logging():
    """Sets up the logging options for a log with supplied name."""

    if CONF.log_config:
        # Use a logging configuration file for all settings...
        if os.path.exists(CONF.log_config):
            logging.config.fileConfig(CONF.log_config)
            return
        else:
            raise RuntimeError(_("Unable to locate specified logging "
                                 "config file: %s") % CONF.log_config)

    root_logger = logging.root
    if CONF.debug:
        root_logger.setLevel(logging.DEBUG)
    elif CONF.verbose:
        root_logger.setLevel(logging.INFO)
    else:
        root_logger.setLevel(logging.WARNING)

    formatter = logging.Formatter(CONF.log_format, CONF.log_date_format)

    if CONF.use_syslog:
        try:
            facility = getattr(logging.handlers.SysLogHandler,
                               CONF.syslog_log_facility)
        except AttributeError:
            raise ValueError(_("Invalid syslog facility"))

        handler = logging.handlers.SysLogHandler(address='/dev/log',
                                                 facility=facility)
    elif CONF.log_file:
        logfile = CONF.log_file
        if CONF.log_dir:
            logfile = os.path.join(CONF.log_dir, logfile)
        handler = logging.handlers.WatchedFileHandler(logfile)
    else:
        handler = logging.StreamHandler(sys.stdout)

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)


def _get_deployment_flavor():
    """Retrieve the paste_deploy.flavor config item, formatted appropriately
       for appending to the application name.
    """
    flavor = CONF.paste_deploy.flavor
    return '' if not flavor else ('-' + flavor)


def _get_paste_config_path():
    paste_suffix = '-paste.ini'
    conf_suffix = '.conf'
    if CONF.config_file:
        # Assume paste config is in a paste.ini file corresponding
        # to the last config file
        path = CONF.config_file[-1].replace(conf_suffix, paste_suffix)
    else:
        path = CONF.prog + '-paste.ini'
    return CONF.find_file(os.path.basename(path))


def _get_deployment_config_file():
    """Retrieve the deployment_config_file config item, formatted as an
       absolute pathname.
    """
    path = CONF.paste_deploy.config_file
    if not path:
        path = _get_paste_config_path()
    if not path:
        msg = _("Unable to locate paste config file for %s.") % CONF.prog
        raise RuntimeError(msg)
    return os.path.abspath(path)


def load_paste_app(app_name=None):
    """Builds and returns a WSGI app from a paste config file.

    We assume the last config file specified in the supplied ConfigOpts
    object is the paste config file.

    :param app_name: name of the application to load

    :raises RuntimeError when config file cannot be located or application
            cannot be loaded from config file
    """
    if app_name is None:
        app_name = CONF.prog

    # append the deployment flavor to the application name,
    # in order to identify the appropriate paste pipeline
    app_name += _get_deployment_flavor()

    conf_file = _get_deployment_config_file()

    try:
        logger = logging.getLogger(__name__)
        logger.debug("Loading %(app_name)s from %(conf_file)s".format(
            conf_file=conf_file, app_name=app_name))

        app = deploy.loadapp("config:%s" % conf_file, name=app_name)

        # Log the options used when starting if we're in debug mode...
        if CONF.debug:
            CONF.log_opt_values(logger, logging.DEBUG)

        return app
    except (LookupError, ImportError) as e:
        msg = _("Unable to load %(app_name)s from configuration file"
                " %(conf_file)s. \nGot: %(e)r") % {'conf_file': conf_file,
                                                   'app_name': app_name,
                                                   'e': e}
        logger.error(msg)
        raise RuntimeError(msg)
