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

import collections
import random
import re
import string
import time

import jsonpatch
import jsonpointer
from oslo_config import cfg as oslo_cfg
from oslo_log import log as logging
from oslo_serialization import base64
import six
from yaql.language import specs
from yaql.language import utils
from yaql.language import yaqltypes

from murano.common import config as cfg
from murano.dsl import constants
from murano.dsl import dsl
from murano.dsl import helpers
from murano.dsl import yaql_integration

from castellan.common import exception as castellan_exception
from castellan.common import utils as castellan_utils
from castellan import key_manager
from castellan import options

LOG = logging.getLogger(__name__)

_random_string_counter = None


@specs.parameter('value', yaqltypes.String())
@specs.extension_method
def base64encode(value):
    return base64.encode_as_text(value)


@specs.parameter('value', yaqltypes.String())
@specs.extension_method
def base64decode(value):
    return base64.decode_as_text(value)


@specs.parameter('collection', yaqltypes.Iterable())
@specs.parameter('composer', yaqltypes.Lambda())
@specs.extension_method
def pselect(collection, composer):
    return helpers.parallel_select(collection, composer)


@specs.parameter('mappings', collections.Mapping)
@specs.extension_method
def bind(obj, mappings):
    if isinstance(obj, six.string_types) and obj.startswith('$'):
        value = _convert_macro_parameter(obj[1:], mappings)
        if value is not None:
            return value
    elif utils.is_sequence(obj):
        return [bind(t, mappings) for t in obj]
    elif isinstance(obj, collections.Mapping):
        result = {}
        for key, value in obj.items():
            result[bind(key, mappings)] = bind(value, mappings)
        return result
    elif isinstance(obj, six.string_types) and obj.startswith('$'):
        value = _convert_macro_parameter(obj[1:], mappings)
        if value is not None:
            return value
    return obj


def _convert_macro_parameter(macro, mappings):
    replaced = [False]

    def replace(match):
        replaced[0] = True
        return six.text_type(mappings.get(match.group(1)))

    result = re.sub('{(\\w+?)}', replace, macro)
    if replaced[0]:
        return result
    else:
        return mappings[macro]


@specs.parameter('group', yaqltypes.String())
@specs.parameter('setting', yaqltypes.String())
@specs.parameter('read_as_file', bool)
def config(group, setting, read_as_file=False):
    config_value = cfg.CONF[group][setting]
    if read_as_file:
        with open(config_value) as target_file:
            return target_file.read()
    else:
        return config_value


@specs.parameter('setting', yaqltypes.String())
@specs.name('config')
def config_default(setting):
    return cfg.CONF[setting]


@specs.parameter('string', yaqltypes.String())
@specs.parameter('start', int)
@specs.parameter('length', int)
@specs.inject('delegate', yaqltypes.Delegate('substring', method=True))
@specs.extension_method
def substr(delegate, string, start, length=-1):
    return delegate(string, start, length)


@specs.extension_method
def patch_(engine, obj, patch):
    if not isinstance(patch, tuple):
        patch = (patch,)
    patch = dsl.to_mutable(patch, engine)
    patch = jsonpatch.JsonPatch(patch)
    try:
        obj = dsl.to_mutable(obj, engine)
        return patch.apply(obj, in_place=True)
    except jsonpointer.JsonPointerException:
        return obj


def _int2base(x, base):
    """Converts decimal integers into another number base

    Converts decimal integers into another number base
    from base-2 to base-36.

    :param x: decimal integer
    :param base: number base, max value is 36
    :return: integer converted to the specified base
    """
    digs = string.digits + string.ascii_lowercase
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
        x //= base
    if sign < 0:
        digits.append('-')
    digits.reverse()
    return ''.join(digits)


def random_name():
    """Replace '#' char in pattern with supplied number

    Replace '#' char in pattern with supplied number. If no pattern is
    supplied, generate a short and unique name for the host.

    :param pattern: hostname pattern
    :param number: number to replace with in pattern
    :return: hostname
    """
    global _random_string_counter

    counter = _random_string_counter or 1
    # generate first 5 random chars
    prefix = ''.join(random.choice(string.ascii_lowercase) for _ in range(5))
    # convert timestamp to higher base to shorten hostname string
    # (up to 8 chars)
    timestamp = _int2base(int(time.time() * 1000), 36)[:8]
    # third part of random name up to 2 chars
    # (1295 is last 2-digit number in base-36, 1296 is first 3-digit number)
    suffix = _int2base(counter, 36)
    _random_string_counter = (counter + 1) % 1296
    return prefix + timestamp + suffix


@specs.parameter('collection', yaqltypes.Iterable())
@specs.parameter('default', nullable=True)
@specs.extension_method
def first_or_default(collection, default=None):
    try:
        return next(iter(collection))
    except StopIteration:
        return default


@specs.parameter('logger_name', yaqltypes.String(True))
def logger(context, logger_name):
    """Instantiate Logger"""
    log = yaql_integration.call_func(
        context, 'new', 'io.murano.system.Logger',
        logger_name=logger_name)
    return log


@specs.parameter('value', yaqltypes.String())
@specs.extension_method
def decrypt_data(value):
    options.set_defaults(oslo_cfg.CONF,
                         barbican_endpoint_type='internal')
    manager = key_manager.API()
    try:
        context = castellan_utils.credential_factory(conf=cfg.CONF)
    except castellan_exception.AuthTypeInvalidError as e:
        LOG.exception(e)
        LOG.error("Castellan must be correctly configured in order to use "
                  "decryptData()")
        raise
    try:
        data = manager.get(context, value).get_encoded()
    except castellan_exception.KeyManagerError as e:
        LOG.exception(e)
        raise
    return data


@helpers.memoize
def get_context(runtime_version):
    context = yaql_integration.create_empty_context()
    context.register_function(base64decode)
    context.register_function(base64encode)
    context.register_function(pselect)
    context.register_function(bind)
    context.register_function(random_name)
    context.register_function(patch_)
    context.register_function(logger)
    context.register_function(decrypt_data, 'decryptData')

    if runtime_version <= constants.RUNTIME_VERSION_1_1:
        context.register_function(substr)
        context.register_function(first_or_default)

        root_context = yaql_integration.create_context(runtime_version)
        for t in ('to_lower', 'to_upper', 'trim', 'join', 'split',
                  'starts_with', 'ends_with', 'matches', 'replace',
                  'flatten'):
            for spec in utils.to_extension_method(t, root_context):
                context.register_function(spec)
    return context


@helpers.memoize
def get_restricted_context():
    context = yaql_integration.create_empty_context()
    context.register_function(config)
    context.register_function(config_default)
    return context
