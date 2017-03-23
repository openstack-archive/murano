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

from oslo_config import cfg
from oslo_log import log as logging
from oslo_middleware import cors

from murano.common.i18n import _
from murano import version


cfapi_opts = [
    cfg.StrOpt('tenant', default='admin',
               help=_('Project for service broker')),
    cfg.HostAddressOpt('bind_host', default='localhost',
                       help=_('Host for service broker')),
    cfg.StrOpt('bind_port', default='8083',
               help=_('Port for service broker')),
    cfg.StrOpt('auth_url', default='localhost:5000',
               help=_('Authentication URL')),
    cfg.StrOpt('user_domain_name', default='default',
               help=_('Domain name of the user')),
    cfg.StrOpt('project_domain_name', default='default',
               help=_('Domain name of the project')),
    cfg.StrOpt('packages_service', default='murano',
               help=_('Package service which should be used by service'
                      ' broker'))]

CONF = cfg.CONF
CONF.register_opts(cfapi_opts, group='cfapi')


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
