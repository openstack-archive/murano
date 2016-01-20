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

import abc

import six


@six.add_metaclass(abc.ABCMeta)
class ModifyActionBase(object):
    """Base class for model modify actions.

    Class is instantiated base on list of actions returned from congress then
    is performed on given object model.

    Base action class initializer doesn't have arguments. However, concrete
    action classes may have any number of parameters defining action behavior.
    These parameters must correspond to parameters returned from congress.

    Action must be registered/exposed to action manager via entry point
    'murano_policy_modify_actions'. Only actions registered via this
    entry point are can be used.
    """

    @abc.abstractmethod
    def modify(self, model):

        """Modifies given object model

        Action parameters are available as instance variables
        passed to initializer.

        :param model: object model to be modified
        """
        pass
