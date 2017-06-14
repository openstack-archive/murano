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

action_policies = [
    policy.DocumentedRuleDefault(
        name='execute_action',
        check_str=base.RULE_DEFAULT,
        description="""Excute an available action on a deployed environment,
retrieve the task status of an executed action, or retrieve the result of
an executed static action.""",
        operations=[
            {'path': 'v1/environments/{environment_id}/actions/{action_id}',
             'method': 'POST'},
            {'path': 'v1/environments/{environment_id}/actions/{task_id}',
             'method': 'GET'},
            {'path': 'v1/actions',
             'method': 'POST'}])
]


def list_rules():
    return action_policies
