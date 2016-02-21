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

import re

import six

TYPE_NAME_RE = re.compile(r'^([a-zA-Z_]\w*:|:)?[a-zA-Z_]\w*(\.[a-zA-Z_]\w*)*$')
NS_RE = re.compile(r'^([a-zA-Z_]\w*(\.[a-zA-Z_]\w*)*)?$')
PREFIX_RE = re.compile(r'^([a-zA-Z_]\w*|=)$')


class NamespaceResolver(object):
    def __init__(self, namespaces):
        if namespaces is None:
            namespaces = {}
        for prefix, ns in namespaces.items():
            if ns is None:
                ns = ''
            if PREFIX_RE.match(prefix) is None:
                raise ValueError(
                    'Invalid namespace prefix "{0}"'.format(prefix))
            if NS_RE.match(ns) is None:
                raise ValueError('Invalid namespace "{0}"'.format(ns))
        self._namespaces = namespaces.copy()
        self._namespaces.setdefault('=', '')
        self._namespaces[''] = ''

    def resolve_name(self, name):
        if not self.is_typename(name, True):
            raise ValueError('Invalid type name "{0}"'.format(name))
        name = six.text_type(name)
        if ':' not in name:
            if '.' in name:
                parts = ['', name]
            else:
                parts = ['=', name]
        else:
            parts = name.split(':')
            if not parts[0]:
                parts[0] = '='

        if parts[0] not in self._namespaces:
            raise KeyError('Unknown namespace prefix ' + parts[0])

        ns = self._namespaces[parts[0]]
        if not ns:
            return parts[1]
        return '.'.join((ns, parts[1]))

    @staticmethod
    def is_typename(name, relaxed):
        if not name:
            return False
        name = six.text_type(name)
        if not relaxed and ':' not in name:
            return False
        return TYPE_NAME_RE.match(name) is not None
