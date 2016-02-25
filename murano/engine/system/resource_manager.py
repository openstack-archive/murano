# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json as jsonlib

import yaml as yamllib
from yaql.language import specs
from yaql.language import yaqltypes

from murano.dsl import dsl
from murano.dsl import dsl_types
from murano.dsl import helpers

if hasattr(yamllib, 'CSafeLoader'):
    yaml_loader = yamllib.CSafeLoader
else:
    yaml_loader = yamllib.SafeLoader


def _construct_yaml_str(self, node):
    # Override the default string handling function
    # to always return unicode objects
    return self.construct_scalar(node)

yaml_loader.add_constructor(u'tag:yaml.org,2002:str', _construct_yaml_str)
# Unquoted dates like 2013-05-23 in yaml files get loaded as objects of type
# datetime.data which causes problems in API layer when being processed by
# oslo.serialization.jsonutils. Therefore, make unicode string out of
# timestamps until jsonutils can handle dates.
yaml_loader.add_constructor(u'tag:yaml.org,2002:timestamp',
                            _construct_yaml_str)


@dsl.name('io.murano.system.Resources')
class ResourceManager(object):
    def __init__(self, context):
        murano_class = helpers.get_type(helpers.get_caller_context(context))
        self._package = murano_class.package

    @staticmethod
    @specs.parameter('owner', dsl.MuranoTypeParameter(nullable=True))
    @specs.inject('receiver', yaqltypes.Receiver())
    def string(receiver, name, owner=None):
        path = ResourceManager._get_package(owner, receiver).get_resource(name)
        with open(path) as file:
            return file.read()

    @classmethod
    @specs.parameter('owner', dsl.MuranoTypeParameter(nullable=True))
    @specs.inject('receiver', yaqltypes.Receiver())
    def json(cls, receiver, name, owner=None):
        return jsonlib.loads(cls.string(receiver, name, owner))

    @classmethod
    @specs.parameter('owner', dsl.MuranoTypeParameter(nullable=True))
    @specs.inject('receiver', yaqltypes.Receiver())
    def yaml(cls, receiver, name, owner=None):
        return yamllib.load(
            cls.string(receiver, name, owner), Loader=yaml_loader)

    @staticmethod
    def _get_package(owner, receiver):
        if owner is None:
            if isinstance(receiver, dsl_types.MuranoObjectInterface):
                return receiver.extension._package
            murano_class = helpers.get_type(helpers.get_caller_context())
        else:
            murano_class = owner.type
        return murano_class.package
