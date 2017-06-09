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

deployment_policies = [
    policy.DocumentedRuleDefault(
        name='list_deployments',
        check_str=base.RULE_DEFAULT,
        description='List deployments for an environment.',
        operations=[{'path': '/v1/environments/{env_id}/deployments',
                     'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        name='list_deployments_all_environments',
        check_str=base.RULE_DEFAULT,
        description='List deployments for all environments in a project.',
        operations=[{'path': '/v1/deployments',
                     'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        name='statuses_deployments',
        check_str=base.RULE_DEFAULT,
        description='Show deployment status details for a deployment.',
        operations=[{
            'path': '/v1/environments/{env_id}/deployments/{deployment_id}',
            'method': 'GET'}])
]


def list_rules():
    return deployment_policies
