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

environment_policies = [
    policy.DocumentedRuleDefault(
        name='list_environments',
        check_str=base.RULE_DEFAULT,
        description='List environments in a project.',
        operations=[{'path': '/v1/environments',
                     'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        name='list_environments_all_tenants',
        check_str=base.RULE_ADMIN_API,
        description='List environments across all projects.',
        operations=[{'path': '/v1/environments?all_tenants=true',
                     'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        name='show_environment',
        check_str=base.RULE_DEFAULT,
        description='Show details for an environment or shows the environment '
                    'model.',
        operations=[{'path': '/v1/environments/{environment_id}',
                     'method': 'GET'},
                    {'path': '/v1/environments/{environment_id}/model',
                     'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        name='update_environment',
        check_str=base.RULE_DEFAULT,
        description='Update or rename an environment.',
        operations=[{'path': '/v1/environments/{environment_id}',
                     'method': 'PUT'},
                    {'path': '/v1/environments/{environment_id}/model',
                     'method': 'PATCH'}]),
    policy.DocumentedRuleDefault(
        name='create_environment',
        check_str=base.RULE_DEFAULT,
        description='Create an environment or create an environment and '
                    'session from an environment template.',
        operations=[
            {'path': '/v1/environments/{environment_id}',
             'method': 'POST'},
            {'path': '/v1/templates/{env_template_id}/create-environment',
             'method': 'POST'}]),
    policy.DocumentedRuleDefault(
        name='delete_environment',
        check_str=base.RULE_DEFAULT,
        description='Delete an environment.',
        operations=[{'path': '/v1/environments/{environment_id}',
                     'method': 'DELETE'}])
]


def list_rules():
    return environment_policies
