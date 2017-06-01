# Copyright 2017 AT&T Corporation.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from oslo_policy import policy

from murano.common.policies import base

template_policies = [
    policy.DocumentedRuleDefault(
        name='list_env_templates',
        check_str=base.RULE_DEFAULT,
        description='List environment templates in a project.',
        operations=[{'path': '/v1/templates',
                     'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        name='create_env_template',
        check_str=base.RULE_DEFAULT,
        description='Create an environment template.',
        operations=[{'path': '/v1/templates',
                     'method': 'POST'}]),
    policy.DocumentedRuleDefault(
        name='show_env_template',
        check_str=base.RULE_DEFAULT,
        description='Show environment template details.',
        operations=[{'path': '/v1/templates/{env_template_id}',
                     'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        name='update_env_template',
        check_str=base.RULE_DEFAULT,
        description='Update an environment template.',
        operations=[{'path': '/v1/templates/{env_template_id}',
                     'method': 'PUT'}]),
    policy.DocumentedRuleDefault(
        name='delete_env_template',
        check_str=base.RULE_DEFAULT,
        description='Delete an environment template.',
        operations=[{'path': '/v1/templates/{env_template_id}',
                     'method': 'DELETE'}]),
    policy.DocumentedRuleDefault(
        name='clone_env_template',
        check_str=base.RULE_DEFAULT,
        description='Clone an environment template.',
        operations=[{'path': '/v1/templates/{env_template_id}/clone',
                     'method': 'POST'}])
]


def list_rules():
    return template_policies
