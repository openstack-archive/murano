# Copyright (c) 2015 Mirantis, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from glance.common.glare import definitions


class MuranoPackage(definitions.ArtifactType):
    __endpoint__ = 'murano'

    type = definitions.String(allowed_values=['Application', 'Library'],
                              required=True,
                              mutable=False)

    author = definitions.String(required=False, mutable=False)
    display_name = definitions.String(required=True, mutable=True)
    enabled = definitions.Boolean(default=True)

    categories = definitions.Array(default=[], mutable=True)
    class_definitions = definitions.Array(unique=True, default=[],
                                          mutable=False)
    inherits = definitions.Dict(default={}, properties=definitions.Array(),
                                mutable=False)
    keywords = definitions.Array(default=[], mutable=True)
    logo = definitions.BinaryObject()
    archive = definitions.BinaryObject()
    ui_definition = definitions.BinaryObject()
