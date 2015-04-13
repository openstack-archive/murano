# Copyright (c) 2014 OpenStack Foundation.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
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

import re

from murano.common.i18n import _, _LI
from murano.openstack.common import log as logging
from murano.policy import congress_rules


LOG = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised for validation errors."""
    pass


class ModelPolicyEnforcer(object):
    """Policy Enforcer Implementation using Congress client

    Converts murano model to list of congress data rules.

    We ask congress using simulation api of congress rest client
    to resolve "murano_system:predeploy_errors(env_id, obj_id, msg)"
    table along with congress data rules to return validation results.
    """

    def __init__(self, environment):
        self._environment = environment
        self._client_manager = environment.clients

    def validate(self, model, class_loader=None):
        """Validate model using Congress rule engine.

        @type model: dict
        @param model: Dictionary representation of model starting on
                      environment level (['Objects'])
        @type class_loader: murano.dsl.class_loader.MuranoClassLoader
        @param class_loader: Optional. Used for evaluating parent class types
        @raises ValidationError in case validation was not successful
        """

        if model is None:
            return

        client = self._client_manager.get_congress_client(self._environment)
        if not client:
            raise ValueError(_('Congress client is not configured!'))

        LOG.info(_LI('Validating model'))
        LOG.debug(model)

        rules = congress_rules.CongressRulesManager().convert(
            model, class_loader, self._environment.tenant_id)

        rules_str = map(str, rules)
        env_id = model['?']['id']
        # cleanup of data populated by murano driver
        rules_str.insert(0, 'deleteEnv("{0}")'.format(env_id))

        rules_line = " ".join(rules_str)
        LOG.debug('Congress rules: \n  ' +
                  '\n  '.join(rules_str))

        validation_result = client.execute_policy_action(
            "murano_system",
            "simulate",
            False,
            False,
            {'query': 'predeploy_errors(eid, oid, msg)',
             'action_policy': 'murano_action',
             'sequence': rules_line})

        if validation_result["result"]:

            messages = self._parse_messages(env_id,
                                            validation_result["result"])

            if messages:
                result_str = "\n  ".join(map(str, messages))
                msg = _("Murano object model validation failed: {0}").format(
                    "\n  " + result_str)
                LOG.error(msg)
                raise ValidationError(msg)
        else:
            LOG.info(_LI('Model valid'))

    def _parse_messages(self, env_id, results):
        """Transforms list of strings in format
            ['predeploy_errors("env_id_1", "obj_id_1", "message1")',
            'predeploy_errors("env_id_2", "obj_id_2", "message2")']
        to list of strings with message only filtered to provided
        env_id (e.g. 'env_id_1'):
            ['message2']
        """

        messages = []
        regexp = 'predeploy_errors\("([^"]*)",\s*"([^"]*)",\s*"([^"]*)"\)'
        for result in results:
            match = re.search(regexp, result)
            if match:
                if env_id in match.group(1):
                    messages.append(match.group(3))

        return messages
