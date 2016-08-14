#    Copyright (c) 2014 Mirantis, Inc.
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

import sys
import weakref

import six

from murano.dsl import dsl_types
from murano.dsl import exceptions
from murano.dsl import helpers
from murano.dsl import meta
from murano.dsl import typespec


class MuranoProperty(dsl_types.MuranoProperty, typespec.Spec,
                     meta.MetaProvider):
    def __init__(self, declaring_type, property_name, declaration):
        super(MuranoProperty, self).__init__(declaration, declaring_type)
        self._property_name = property_name
        self._declaring_type = weakref.ref(declaring_type)
        self._usage = declaration.get('Usage') or dsl_types.PropertyUsages.In
        if self._usage not in dsl_types.PropertyUsages.All:
            raise exceptions.DslSyntaxError(
                'Unknown usage {0}. Must be one of ({1})'.format(
                    self._usage, ', '.join(dsl_types.PropertyUsages.All)))
        self._meta = meta.MetaData(
            declaration.get('Meta'),
            dsl_types.MetaTargets.Property, declaring_type)
        self._meta_values = None

    def transform(self, *args, **kwargs):
        try:
            return super(MuranoProperty, self).transform(*args, **kwargs)
        except exceptions.ContractViolationException as e:
            msg = u'[{0}.{1}{2}] {3}'.format(
                self.declaring_type.name, self.name, e.path, six.text_type(e))
            six.reraise(exceptions.ContractViolationException,
                        exceptions.ContractViolationException(msg),
                        sys.exc_info()[2])

    @property
    def name(self):
        return self._property_name

    @property
    def usage(self):
        return self._usage

    def get_meta(self, context):
        def meta_producer(cls):
            prop = cls.properties.get(self.name)
            if prop is None:
                return None
            return prop._meta

        if self._meta_values is None:
            executor = helpers.get_executor()
            context = executor.create_type_context(
                self.declaring_type, caller_context=context)

            self._meta_values = meta.merge_providers(
                self.declaring_type, meta_producer, context)
        return self._meta_values

    def __repr__(self):
        return 'MuranoProperty({type}::{name})'.format(
            type=self.declaring_type.name, name=self.name)
