#    Copyright (c) 2013 Mirantis, Inc.
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

import collections
import functools as func
import re

import jsonschema
from oslo_log import log as logging
import six

from murano.common.i18n import _


LOG = logging.getLogger(__name__)


class TraverseHelper(object):
    value_type = (six.string_types, int, float, bool)

    @staticmethod
    def get(path, source):
        """Provides the ability to traverse a data source

        Provides the ability to traverse a data source made up of any
        combination of lists and dicts. Has simple rules for selecting item of
        the list:

        * each item should have id property
        * to select item from the list, specify id value

        Examples:
            source = {'obj': {'attr': True}}
            value = TraverseHelper.get('/obj/attr', source)

            source = {'obj': [
                {'id': '1', 'value': 1},
                {'id': '2s', 'value': 2},
            ]}
            value = TraverseHelper.get('/obj/2s/value', source)


        :param path: string with path to desired value
        :param source: python object (list or dict)
        :return: object
        :raise: ValueError if object is malformed
        """
        queue = collections.deque(filter(lambda x: x, path.split('/')))

        while len(queue):
            path = queue.popleft()

            if isinstance(source, list):
                idx_source = source
                iterator = (
                    i for i in source
                    if i.get('?', {}).get('id') == path
                )
                source = next(iterator, None)
                if source is None and path.isdigit():
                    source = idx_source[int(path)]
            elif isinstance(source, dict):
                source = source[path]
            elif isinstance(source, TraverseHelper.value_type):
                break
            else:
                raise ValueError(_('Source object or path is malformed'))

        return source

    @staticmethod
    def update(path, value, source):
        """Updates value selected with specified path.

        Warning: Root object could not be updated

        :param path: string with path to desired value
        :param value: value
        :param source: python object (list or dict)
        """
        parent_path = '/'.join(path.split('/')[:-1])
        node = TraverseHelper.get(parent_path, source)
        key = path[1:].split('/')[-1]
        if is_number(key):
            node[int(key)] = value
        else:
            node[key] = value

    @staticmethod
    def insert(path, value, source):
        """Inserts new item to selected list.

        :param path: string with path to desired value
        :param value: value
        :param source: List
        """
        node = TraverseHelper.get(path, source)
        node.append(value)

    @staticmethod
    def extend(path, value, source):
        """Extend list by appending elements from the iterable.

        :param path: string with path to desired value
        :param value: value
        :param source: List
        """
        node = TraverseHelper.get(path, source)
        node.extend(value)

    @staticmethod
    def remove(path, source):
        """Removes selected item from source.

        :param path: string with path to desired value
        :param source: python object (list or dict)
        """
        parent_path = '/'.join(path.split('/')[:-1])
        node = TraverseHelper.get(parent_path, source)
        key = path[1:].split('/')[-1]

        if isinstance(node, list):
            iterator = (i for i in node if i.get('?', {}).get('id') == key)
            item = next(iterator, None)
            if item is None and key.isdigit():
                del node[int(key)]
            else:
                node.remove(item)
        elif isinstance(node, dict):
            del node[key]
        else:
            raise ValueError(_('Source object or path is malformed'))


def is_number(var):
    try:
        int(var)
        return True
    except Exception:
        return False


def is_different(obj1, obj2):
    """Stripped-down version of deep.diff comparator

    Compares arbitrary nested objects, handles circular links, but doesn't
    point to the first difference as deep.diff does.
    """
    class Difference(Exception):
        pass

    def is_in(o, st):
        for _o in st:
            if o is _o:
                return True
        return False

    def rec(o1, o2, stack1=(), stack2=()):
        if is_in(o1, stack1) and is_in(o2, stack2):
            # circular reference detected - break the loop
            return
        elif is_in(o1, stack1):
            raise Difference()
        else:
            stack1 += (o1,)
            stack2 += (o2,)

        if o1 is o2:
            return
        elif (isinstance(o1, six.string_types) and
                isinstance(o2, six.string_types)) and o1 == o2:
            return
        elif type(o1) != type(o2):
            raise Difference()
        elif isinstance(o1, dict):
            # check for keys inequality
            rec(o1.keys(), o2.keys(), stack1, stack2)
            for key in o1.keys():
                rec(o1[key], o2[key], stack1, stack2)
        elif isinstance(o1, (list, tuple, set)):
            if len(o1) != len(o2):
                raise Difference()
            else:
                for _o1, _o2 in zip(o1, o2):
                    rec(_o1, _o2, stack1, stack2)
        elif hasattr(o1, '__dict__'):
            return rec(o1.__dict__, o2.__dict__, stack1, stack2)
        elif o1 != o2:
            raise Difference()

    try:
        rec(obj1, obj2)
    except Difference:
        return True
    else:
        return False


def build_entity_map(value):
    def build_entity_map_recursive(value, id_map):
        if isinstance(value, dict):
            if '?' in value and 'id' in value['?']:
                id_map[value['?']['id']] = value
            for v in value.values():
                build_entity_map_recursive(v, id_map)
        if isinstance(value, list):
            for item in value:
                build_entity_map_recursive(item, id_map)

    id_map = {}
    build_entity_map_recursive(value, id_map)
    return id_map


def handle(f):
    """Handles exception in wrapped function and writes to LOG."""

    @func.wraps(f)
    def f_handle(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            LOG.exception(e)

    return f_handle


def validate_body(schema):
    def deco_validate_body(f):
        @func.wraps(f)
        def f_validate_body(*args, **kwargs):
            if 'body' in kwargs:
                jsonschema.validate(kwargs['body'], schema)
                return f(*args, **kwargs)
        return f_validate_body
    return deco_validate_body


def validate_quotes(value):
    """Validate filter values

    Validation opening/closing quotes in the expression.
    """
    open_quotes = True
    count_backslash_in_row = 0
    for i in range(len(value)):
        if value[i] == '"':
            if count_backslash_in_row % 2:
                continue
            if open_quotes:
                if i and value[i - 1] != ',':
                    msg = _("Invalid filter value %s. There is no comma "
                            "before opening quotation mark.") % value
                    raise ValueError(msg)
            else:
                if i + 1 != len(value) and value[i + 1] != ",":
                    msg = _("Invalid filter value %s. There is no comma "
                            "after opening quotation mark.") % value
                    raise ValueError(msg)
            open_quotes = not open_quotes
        elif value[i] == '\\':
            count_backslash_in_row += 1
        else:
            count_backslash_in_row = 0
    if not open_quotes:
        msg = _("Invalid filter value %s. The quote is not closed.") % value
        raise ValueError(msg)
    return True


def split_for_quotes(value):
    """Split filter values

    Split values by commas and quotes for 'in' operator, according api-wg.
    """
    validate_quotes(value)
    tmp = re.compile(r'''
        "(                 # if found a double-quote
           [^\"\\]*        # take characters either non-quotes or backslashes
           (?:\\.          # take backslashes and character after it
            [^\"\\]*)*     # take characters either non-quotes or backslashes
         )                 # before double-quote
        ",?                # a double-quote with comma maybe
        | ([^,]+),?        # if not found double-quote take any non-comma
                           # characters with comma maybe
        | ,                # if we have only comma take empty string
        ''', re.VERBOSE)
    val_split = [val[0] or val[1] for val in re.findall(tmp, value)]
    replaced_inner_quotes = [s.replace(r'\"', '"') for s in val_split]
    return replaced_inner_quotes
