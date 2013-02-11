# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
# All Rights Reserved.
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
"""Base classes and custome fields for balancer models."""

import json

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import object_mapper
from sqlalchemy.types import TypeDecorator
from sqlalchemy import Text


Base = declarative_base()


class DictBase(object):
    def to_dict(self):
        return dict(self.iteritems())

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __iter__(self):
        return (col.name for col in object_mapper(self).columns)

    def keys(self):
        return list(self)

    def update(self, values):
        for key, value in values.iteritems():
            if isinstance(value, dict):
                value = value.copy()
            setattr(self, key, value)

    def iteritems(self):
        items = []
        for key in self:
            value = getattr(self,  key)
            if isinstance(value, dict):
                value = value.copy()
            items.append((key, value))
        return iter(items)


class JsonBlob(TypeDecorator):

    impl = Text

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)
