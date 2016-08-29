#    Copyright (c) 2016 Mirantis, Inc.
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

from yaql.language import specs
from yaql.language import yaqltypes

from murano.dsl import contracts
from murano.dsl import exceptions
from murano.dsl import helpers


class Check(contracts.ContractMethod):
    name = 'check'

    @specs.parameter('predicate', yaqltypes.Lambda(with_context=True))
    @specs.parameter('msg', yaqltypes.String(nullable=True))
    def __init__(self, predicate, msg=None):
        self.predicate = predicate
        self.msg = msg

    def validate(self):
        if isinstance(self.value, contracts.ObjRef) or self.predicate(
                self.root_context.create_child_context(), self.value):
            return self.value
        else:
            msg = self.msg
            if not msg:
                msg = "Value {0} doesn't match predicate".format(
                    helpers.format_scalar(self.value))
            raise exceptions.ContractViolationException(msg)

    def transform(self):
        return self.validate()
