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


import copy
import itertools


import murano.common.config
import murano.common.wsgi
import murano.openstack.common.log
import murano.openstack.common.policy
import murano.openstack.common.sslutils


def build_list(opt_list):
    return list(itertools.chain(*opt_list))


# List of *all* options in [DEFAULT] namespace of murano.
# Any new option list or option needs to be registered here.
_opt_lists = [
    ('engine', murano.common.config.engine_opts),
    ('rabbitmq', murano.common.config.rabbit_opts),
    ('heat', murano.common.config.heat_opts),
    ('neutron', murano.common.config.neutron_opts),
    ('keystone', murano.common.config.keystone_opts),
    ('murano', murano.common.config.murano_opts),
    ('networking', murano.common.config.networking_opts),
    ('stats', murano.common.config.stats_opts),
    ('packages_opts', murano.common.config.packages_opts),
    ('ssl', murano.openstack.common.sslutils.ssl_opts),
    (None, build_list([
        murano.common.config.metadata_dir,
        murano.common.config.bind_opts,
        murano.common.config.file_server,
        murano.common.wsgi.wsgi_opts,
        murano.openstack.common.log.common_cli_opts,
        murano.openstack.common.log.generic_log_opts,
        murano.openstack.common.log.log_opts,
        murano.openstack.common.log.logging_cli_opts,
        murano.openstack.common.policy.policy_opts
    ])),
]


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
