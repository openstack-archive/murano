# Copyright (c) 2015 OpenStack Foundation.
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

from oslo_log import log as logging
from oslo_utils import importutils
from stevedore import extension
import yaml

LOG = logging.getLogger(__name__)


class ModifyActionManager(object):
    """Manages modify actions

    The manager encapsulates extensible plugin mechanism for
    modify actions loading. Provides ability to apply action on
    given object model based on action specification retrieved
    from congress
    """

    def __init__(self):
        self._cache = {}

    def load_action(self, name):
        """Loads action by its name

        Loaded actions are cached. Plugin mechanism is based on
        distutils entry points. Entry point namespace is
        'murano_policy_modify_actions'

        :param name: action name
        :return:
        """
        if name in self._cache:
            return self._cache[name]
        action = self._load_action(name)
        self._cache[name] = action
        return action

    @staticmethod
    def _load_action(name):
        mgr = extension.ExtensionManager(
            namespace='murano_policy_modify_actions',
            invoke_on_load=False
        )
        for ext in mgr.extensions:
            if name == ext.name:
                target = ext.entry_point_target.replace(':', '.')
                return importutils.import_class(target)
        raise ValueError('No such action definition: {action_name}'
                         .format(action_name=name))

    def apply_action(self, obj, action_spec):
        """Apply action on given model

        Parse action and its parameters from action specification
        retrieved from congress. Action specification is YAML format.

        E.g. remove-object: {object_id: abc123}")

        Action names are keys in top-level dictionary. Values are
        dictionaries containing key/value parameters of the action

        :param obj: subject of modification
        :param action_spec: YAML action spec
        :raise ValueError: in case of malformed action spec
        """
        actions = yaml.safe_load(action_spec)
        if not isinstance(actions, dict):
            raise ValueError('Expected action spec format is '
                             '"action-name: {{p1: v1, ...}}" '
                             'but got "{action_spec}"'
                             .format(action_spec=action_spec))
        for name, kwargs in actions.items():
            LOG.debug('Executing action {name}, params {params}'
                      .format(name=name, params=kwargs))
            # loads action class
            action_class = self.load_action(name)
            # creates action instance
            action_instance = action_class(**kwargs)
            # apply action on object model
            action_instance.modify(obj)
