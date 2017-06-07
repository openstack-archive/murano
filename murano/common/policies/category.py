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

category_policies = [
    policy.DocumentedRuleDefault(
        name='get_category',
        check_str=base.RULE_DEFAULT,
        description="""Show category details or list all categories in the
application catalog.""",
        operations=[{'path': '/v1/catalog/categories/{category_id}',
                     'method': 'GET'},
                    {'path': '/v1/catalog/categories', 'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        name='delete_category',
        check_str=base.RULE_ADMIN_API,
        description='Delete a category.',
        operations=[{'path': '/v1/catalog/categories/{category_id}',
                     'method': 'DELETE'}]),
    policy.DocumentedRuleDefault(
        name='add_category',
        check_str=base.RULE_ADMIN_API,
        description='Create a category.',
        operations=[{'path': '/v1/catalog/categories', 'method': 'POST'}])
]


def list_rules():
    return category_policies
