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

import base64
import collections
import itertools
import random
import re
import string
import time
import types

import jsonpatch
import jsonpointer
import yaql.context

import murano.common.config as cfg
import murano.dsl.helpers as helpers


_random_string_counter = None


def _transform_json(json, mappings):
    if isinstance(json, types.ListType):
        return [_transform_json(t, mappings) for t in json]

    if isinstance(json, types.DictionaryType):
        result = {}
        for key, value in json.items():
            result[_transform_json(key, mappings)] = \
                _transform_json(value, mappings)
        return result

    elif isinstance(json, types.ListType):
        result = []
        for value in json:
            result.append(_transform_json(value, mappings))
        return result

    elif isinstance(json, types.StringTypes) and json.startswith('$'):
        value = _convert_macro_parameter(json[1:], mappings)
        if value is not None:
            return value

    return json


def _convert_macro_parameter(macro, mappings):
    replaced = [False]

    def replace(match):
        replaced[0] = True
        return unicode(mappings.get(match.group(1)))

    result = re.sub('{(\\w+?)}', replace, macro)
    if replaced[0]:
        return result
    else:
        return mappings[macro]


@yaql.context.EvalArg('format', types.StringTypes)
def _format(format, *args):
    return format.format(*[t() for t in args])


@yaql.context.EvalArg('src', types.StringTypes)
@yaql.context.EvalArg('substring', types.StringTypes)
@yaql.context.EvalArg('value', types.StringTypes)
def _replace_str(src, substring, value):
    return src.replace(substring, value)


@yaql.context.EvalArg('src', types.StringTypes)
@yaql.context.EvalArg('replacements', dict)
def _replace_dict(src, replacements):
    for key, value in replacements.iteritems():
        if isinstance(src, str):
            src = src.replace(key, str(value))
        else:
            src = src.replace(key, unicode(value))
    return src


def _len(value):
    return len(value())


def _coalesce(*args):
    for t in args:
        val = t()
        if val:
            return val
    return None


@yaql.context.EvalArg('value', types.StringTypes)
def _base64encode(value):
    return base64.b64encode(value)


@yaql.context.EvalArg('value', types.StringTypes)
def _base64decode(value):
    return base64.b64decode(value)


@yaql.context.EvalArg('group', types.StringTypes)
@yaql.context.EvalArg('setting', types.StringTypes)
def _config(group, setting):
    return cfg.CONF[group][setting]


@yaql.context.EvalArg('setting', types.StringTypes)
def _config_default(setting):
    return cfg.CONF[setting]


@yaql.context.EvalArg('value', types.StringTypes)
def _upper(value):
    return value.upper()


@yaql.context.EvalArg('value', types.StringTypes)
def _lower(value):
    return value.lower()


@yaql.context.EvalArg('separator', types.StringTypes)
def _join(separator, collection):
    return separator.join(str(t) for t in collection())


@yaql.context.EvalArg('value', types.StringTypes)
@yaql.context.EvalArg('separator', types.StringTypes)
def _split(value, separator):
    return value.split(separator)


@yaql.context.EvalArg('value', types.StringTypes)
@yaql.context.EvalArg('prefix', types.StringTypes)
def _startswith(value, prefix):
    return value.startswith(prefix)


@yaql.context.EvalArg('value', types.StringTypes)
@yaql.context.EvalArg('suffix', types.StringTypes)
def _endswith(value, suffix):
    return value.endswith(suffix)


@yaql.context.EvalArg('value', types.StringTypes)
def _trim(value):
    return value.strip()


@yaql.context.EvalArg('value', types.StringTypes)
@yaql.context.EvalArg('pattern', types.StringTypes)
def _mathces(value, pattern):
    return re.match(pattern, value) is not None


@yaql.context.EvalArg('value', types.StringTypes)
@yaql.context.EvalArg('index', int)
@yaql.context.EvalArg('length', int)
def _substr3(value, index, length):
    if length < 0:
        return value[index:]
    else:
        return value[index:index + length]


@yaql.context.EvalArg('value', types.StringTypes)
@yaql.context.EvalArg('index', int)
def _substr2(value, index):
    return _substr3(value, index, -1)


def _str(value):
    value = value()
    if value is None:
        return ''
    elif value is True:
        return 'true'
    elif value is False:
        return 'false'
    return unicode(value)


def _int(value):
    value = value()
    if value is None:
        return 0
    return int(value)


def _pselect(collection, composer):
    if isinstance(collection, types.ListType):
        return helpers.parallel_select(collection, composer)
    else:
        return helpers.parallel_select(collection(), composer)


def _patch(obj, patch):
    obj = obj()
    patch = patch()
    if not isinstance(patch, types.ListType):
        patch = [patch]
    patch = jsonpatch.JsonPatch(patch)
    try:
        return patch.apply(obj)
    except jsonpointer.JsonPointerException:
        return obj


def _int2base(x, base):
    """Converts decimal integers into another number base
     from base-2 to base-36.

    :param x: decimal integer
    :param base: number base, max value is 36
    :return: integer converted to the specified base
    """
    digs = string.digits + string.lowercase
    if x < 0:
        sign = -1
    elif x == 0:
        return '0'
    else:
        sign = 1
    x *= sign
    digits = []
    while x:
        digits.append(digs[x % base])
        x /= base
    if sign < 0:
        digits.append('-')
    digits.reverse()
    return ''.join(digits)


def _random_name():
    """Replace '#' char in pattern with supplied number, if no pattern is
       supplied generate short and unique name for the host.

    :param pattern: hostname pattern
    :param number: number to replace with in pattern
    :return: hostname
    """
    global _random_string_counter

    counter = _random_string_counter or 1
    # generate first 5 random chars
    prefix = ''.join(random.choice(string.lowercase) for _ in range(5))
    # convert timestamp to higher base to shorten hostname string
    # (up to 8 chars)
    timestamp = _int2base(int(time.time() * 1000), 36)[:8]
    # third part of random name up to 2 chars
    # (1295 is last 2-digit number in base-36, 1296 is first 3-digit number)
    suffix = _int2base(counter, 36)
    _random_string_counter = (counter + 1) % 1296
    return prefix + timestamp + suffix


@yaql.context.EvalArg('self', dict)
def _values(self):
    return self.values()


@yaql.context.EvalArg('self', dict)
def _keys(self):
    return self.keys()


@yaql.context.EvalArg('self', collections.Iterable)
def _flatten(self):
    for i in self:
        if isinstance(i, collections.Iterable):
            for ii in i:
                yield ii
        else:
            yield i


@yaql.context.EvalArg('self', dict)
@yaql.context.EvalArg('other', dict)
def _merge_with(self, other):
    return helpers.merge_dicts(self, other)


@yaql.context.EvalArg('collection', collections.Iterable)
@yaql.context.EvalArg('count', int)
def _skip(collection, count):
    return itertools.islice(collection, count, None)


@yaql.context.EvalArg('collection', collections.Iterable)
@yaql.context.EvalArg('count', int)
def _take(collection, count):
    return itertools.islice(collection, count)


@yaql.context.EvalArg('collection', collections.Iterable)
def _aggregate(collection, selector):
    return reduce(selector, collection)


@yaql.context.EvalArg('collection', collections.Iterable)
def _aggregate_with_seed(collection, selector, seed):
    return reduce(selector, collection, seed())


@yaql.context.EvalArg('collection', collections.Iterable)
def _first(collection):
    return iter(collection).next()


@yaql.context.EvalArg('collection', collections.Iterable)
def _first_or_default(collection):
    try:
        return iter(collection).next()
    except StopIteration:
        return None


@yaql.context.EvalArg('collection', collections.Iterable)
def _first_or_default2(collection, default):
    try:
        return iter(collection).next()
    except StopIteration:
        return default


def register(context):
    context.register_function(
        lambda json, mappings: _transform_json(json(), mappings()), 'bind')

    context.register_function(_format, 'format')
    context.register_function(_replace_str, 'replace')
    context.register_function(_replace_dict, 'replace')
    context.register_function(_len, 'len')
    context.register_function(_coalesce, 'coalesce')
    context.register_function(_base64decode, 'base64decode')
    context.register_function(_base64encode, 'base64encode')
    context.register_function(_config, 'config')
    context.register_function(_config_default, 'config')
    context.register_function(_lower, 'toLower')
    context.register_function(_upper, 'toUpper')
    context.register_function(_join, 'join')
    context.register_function(_split, 'split')
    context.register_function(_pselect, 'pselect')
    context.register_function(_startswith, 'startsWith')
    context.register_function(_endswith, 'endsWith')
    context.register_function(_trim, 'trim')
    context.register_function(_mathces, 'matches')
    context.register_function(_substr2, 'substr')
    context.register_function(_substr3, 'substr')
    context.register_function(_str, 'str')
    context.register_function(_int, 'int')
    context.register_function(_patch, 'patch')
    context.register_function(_random_name, 'randomName')
    # Temporary workaround, these functions should be moved to YAQL
    context.register_function(_keys, 'keys')
    context.register_function(_values, 'values')
    context.register_function(_flatten, 'flatten')
    context.register_function(_merge_with, 'mergeWith')
    context.register_function(_skip, 'skip')
    context.register_function(_take, 'take')
    context.register_function(_aggregate, 'aggregate')
    context.register_function(_aggregate_with_seed, 'aggregate')
    context.register_function(_first, 'first')
    context.register_function(_first_or_default, 'firstOrDefault')
    context.register_function(_first_or_default2, 'firstOrDefault')
