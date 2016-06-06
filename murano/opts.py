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

__all__ = [
    'list_opts',
    'list_cfapi_opts',
]

import copy
import itertools

import oslo_service.sslutils

import murano.api.middleware.ssl
import murano.common.cf_config
import murano.common.config
import murano.common.wsgi


def build_list(opt_list):
    return list(itertools.chain(*opt_list))


# List of *all* options in [DEFAULT] namespace of murano.
# Any new option list or option needs to be registered here.
_opt_lists = [
    ('engine', murano.common.config.engine_opts),
    ('rabbitmq', murano.common.config.rabbit_opts),
    ('heat', murano.common.config.heat_opts),
    ('neutron', murano.common.config.neutron_opts),
    ('murano', murano.common.config.murano_opts),
    ('glare', murano.common.config.glare_opts),
    ('mistral', murano.common.config.mistral_opts),
    ('networking', murano.common.config.networking_opts),
    ('stats', murano.common.config.stats_opts),
    (None, build_list([
        murano.common.config.metadata_dir,
        murano.common.config.bind_opts,
        murano.common.config.file_server,
        murano.common.wsgi.wsgi_opts,
        murano.api.middleware.ssl.ssl_middleware_opts
    ])),
]

_cfapi_opt_lists = [
    ('cfapi', murano.common.cf_config.cfapi_opts),
]

_opt_lists.extend(oslo_service.sslutils.list_opts())


def list_opts():
    """Return a list of oslo.config options available in Murano.

    Each element of the list is a tuple. The first element is the name of the
    group under which the list of elements in the second element will be
    registered. A group name of None corresponds to the [DEFAULT] group in
    config files.

    This function is also discoverable via the 'murano' entry point
    under the 'oslo.config.opts' namespace.

    The purpose of this is to allow tools like the Oslo sample config file
    generator to discover the options exposed to users by Murano.

    :returns: a list of (group_name, opts) tuples
    """
    return [(g, copy.deepcopy(o)) for g, o in _opt_lists]


def list_cfapi_opts():
    """Return a list of oslo_config options available in service broker."""
    return [(g, copy.deepcopy(o)) for g, o in _cfapi_opt_lists]
