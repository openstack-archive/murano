#    Copyright (c) 2015 Mirantis, Inc.
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

from yaql.language import contexts
from yaql.language import utils


class LinkedContext(contexts.ContextBase):
    """Context that is as a proxy to another context but has its own parent."""

    def __init__(self, parent_context, linked_context, convention=None):
        self.linked_context = linked_context
        if linked_context.parent:
            super(LinkedContext, self).__init__(
                LinkedContext(parent_context, linked_context.parent,
                              convention), convention)
        else:
            super(LinkedContext, self).__init__(parent_context, convention)

    def register_function(self, spec, *args, **kwargs):
        return self.linked_context.register_function(spec, *args, **kwargs)

    def keys(self):
        return self.linked_context.keys()

    def get_data(self, name, default=None, ask_parent=True):
        result = self.linked_context.get_data(
            name, default=utils.NO_VALUE, ask_parent=False)
        if result is utils.NO_VALUE:
            if not ask_parent or not self.parent:
                return default
            return self.parent.get_data(name, default=default, ask_parent=True)
        return result

    def get_functions(self, name, predicate=None, use_convention=False):
        return self.linked_context.get_functions(
            name, predicate=predicate, use_convention=use_convention)

    def delete_function(self, spec):
        return self.linked_context.delete_function(spec)

    def __contains__(self, item):
        return item in self.linked_context

    def __delitem__(self, name):
        del self.linked_context[name]

    def __setitem__(self, name, value):
        self.linked_context[name] = value

    def create_child_context(self):
        return type(self.linked_context)(self)


def link(parent_context, context):
    if not context:
        return parent_context
    return LinkedContext(parent_context, context)
