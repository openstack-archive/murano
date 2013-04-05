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

from glazierclient.common import utils


def do_environment_list(cc, args={}):
    """List the environments"""
    environments = cc.environments.list()
    field_labels = ['ID', 'Name', 'Created', 'Updated']
    fields = ['id', 'name', 'created', 'updated']
    utils.print_list(environments, fields, field_labels, sortby=0)
