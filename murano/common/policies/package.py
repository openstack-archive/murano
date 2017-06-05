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

package_policies = [
    policy.DocumentedRuleDefault(
        name='get_package',
        check_str=base.RULE_DEFAULT,
        description="""Returns either detailed package information or
information specific to the package's UI or logo. In addition, checks for the
existence of a given package.""",
        operations=[{'path': '/v1/catalog/packages/{package_id}',
                     'method': 'GET'},
                    {'path': '/v1/catalog/packages',
                     'method': 'GET'},
                    {'path': '/v1/catalog/packages/{package_id}/ui',
                     'method': 'GET'},
                    {'path': '/v1/catalog/packages/{package_id}/logo',
                     'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        name='upload_package',
        check_str=base.RULE_DEFAULT,
        description='Upload a package to the application catalog.',
        operations=[{'path': '/v1/catalog/packages',
                     'method': 'POST'}]),
    policy.DocumentedRuleDefault(
        name='modify_package',
        check_str=base.RULE_DEFAULT,
        description='Update package information for a given package.',
        operations=[{'path': '/v1/catalog/packages/{package_id}',
                     'method': 'PATCH'}]),
    policy.DocumentedRuleDefault(
        name='publicize_package',
        check_str=base.RULE_ADMIN_API,
        description="""Publicize a package across all projects. Grants users in
any project the ability to use the package. Enforced only when `is_public`
parameter is set to True in the request body of the `update` or `upload`
package request.""",
        operations=[{'path': '/v1/catalog/packages/{package_id}',
                     'method': 'PATCH'},
                    {'path': '/v1/catalog/packages',
                     'method': 'POST'}]),
    policy.DocumentedRuleDefault(
        name='manage_public_package',
        check_str=base.RULE_DEFAULT,
        description="""Either update, delete or check for the existence of a
public package. Only enforced when the package is public.""",
        operations=[{'path': '/v1/catalog/packages/{package_id}',
                     'method': 'PATCH'},
                    {'path': '/v1/catalog/packages/{package_id}',
                     'method': 'DELETE'},
                    {'path': '/v1/catalog/packages',
                     'method': 'GET'}]),
    policy.DocumentedRuleDefault(
        name='delete_package',
        check_str=base.RULE_DEFAULT,
        description='Delete a given package.',
        operations=[{'path': '/v1/catalog/packages/{package_id}',
                     'method': 'DELETE'}]),
    policy.DocumentedRuleDefault(
        name='download_package',
        check_str=base.RULE_DEFAULT,
        description='Download a package from the application catalog.',
        operations=[{'path': '/v1/catalog/packages/{package_id}/download',
                     'method': 'GET'}])
]


def list_rules():
    return package_policies
