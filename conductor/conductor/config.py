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
Routines for configuring Glance
"""

import logging
import logging.config
import logging.handlers
import os
import sys

from oslo.config import cfg
from paste import deploy

from conductor.version import version_info as version
from ConfigParser import SafeConfigParser

paste_deploy_opts = [
    cfg.StrOpt('flavor'),
    cfg.StrOpt('config_file'),
]

rabbit_opts = [
    cfg.StrOpt('host', default='localhost'),
    cfg.IntOpt('port', default=5672),
    cfg.StrOpt('login', default='guest'),
    cfg.StrOpt('password', default='guest'),
    cfg.StrOpt('virtual_host', default='/'),
]

heat_opts = [
    cfg.StrOpt('auth_url'),
]

CONF = cfg.CONF
CONF.register_opts(paste_deploy_opts, group='paste_deploy')
CONF.register_opts(rabbit_opts, group='rabbitmq')
CONF.register_opts(heat_opts, group='heat')


CONF.import_opt('verbose', 'conductor.openstack.common.log')
CONF.import_opt('debug', 'conductor.openstack.common.log')
CONF.import_opt('log_dir', 'conductor.openstack.common.log')
CONF.import_opt('log_file', 'conductor.openstack.common.log')
CONF.import_opt('log_config', 'conductor.openstack.common.log')
CONF.import_opt('log_format', 'conductor.openstack.common.log')
CONF.import_opt('log_date_format', 'conductor.openstack.common.log')
CONF.import_opt('use_syslog', 'conductor.openstack.common.log')
CONF.import_opt('syslog_log_facility', 'conductor.openstack.common.log')


def parse_args(args=None, usage=None, default_config_files=None):
    CONF(args=args,
         project='conductor',
         version=version.cached_version_string(),
         usage=usage,
         default_config_files=default_config_files)


def setup_logging():
    """
    Sets up the logging options for a log with supplied name
    """

    if CONF.log_config:
        # Use a logging configuration file for all settings...
        if os.path.exists(CONF.log_config):
            logging.config.fileConfig(CONF.log_config)
            return
        else:
            raise RuntimeError("Unable to locate specified logging "
                               "config file: %s" % CONF.log_config)

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
    """
    Retrieve the paste_deploy.flavor config item, formatted appropriately
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
    """
    Retrieve the deployment_config_file config item, formatted as an
    absolute pathname.
    """
    path = CONF.paste_deploy.config_file
    if not path:
        path = _get_paste_config_path()
    if not path:
        msg = "Unable to locate paste config file for %s." % CONF.prog
        raise RuntimeError(msg)
    return os.path.abspath(path)


def load_paste_app(app_name=None):
    """
    Builds and returns a WSGI app from a paste config file.

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
        logger.debug(_("Loading %(app_name)s from %(conf_file)s"),
                     {'conf_file': conf_file, 'app_name': app_name})

        app = deploy.loadapp("config:%s" % conf_file, name=app_name)

        # Log the options used when starting if we're in debug mode...
        if CONF.debug:
            CONF.log_opt_values(logger, logging.DEBUG)

        return app
    except (LookupError, ImportError), e:
        msg = _("Unable to load %(app_name)s from "
                "configuration file %(conf_file)s."
                "\nGot: %(e)r") % locals()
        logger.error(msg)
        raise RuntimeError(msg)


class Config(object):
    CONFIG_PATH = './etc/app.config'

    def __init__(self, filename=None):
        self.config = SafeConfigParser()
        self.config.read(filename or self.CONFIG_PATH)

    def get_setting(self, section, name, default=None):
        if not self.config.has_option(section, name):
            return default
        return self.config.get(section, name)

    def __getitem__(self, item):
        parts = item.rsplit('.', 1)
        return self.get_setting(
            parts[0] if len(parts) == 2 else 'DEFAULT', parts[-1])
