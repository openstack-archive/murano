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


class NamespaceResolver(object):
    def __init__(self, namespaces):
        self._namespaces = namespaces
        self._namespaces[''] = ''

    def resolve_name(self, name, relative=None):
        if name is None:
            raise ValueError()
        if name and name.startswith(':'):
            return name[1:]
        if ':' in name:
            parts = name.split(':')
            if len(parts) != 2 or not parts[1]:
                raise NameError('Incorrectly formatted name ' + name)
            if parts[0] not in self._namespaces:
                raise KeyError('Unknown namespace prefix ' + parts[0])
            return '.'.join((self._namespaces[parts[0]], parts[1]))
        if not relative and '=' in self._namespaces and '.' not in name:
            return '.'.join((self._namespaces['='], name))
        if relative and '.' not in name:
            return '.'.join((relative, name))
        return name
