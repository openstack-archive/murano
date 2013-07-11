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

import eventlet
from jsonschema import validate
from muranoapi.common.uuidutils import generate_uuid
import types
from collections import deque
from functools import wraps
from muranoapi.openstack.common import log as logging

log = logging.getLogger(__name__)


class TraverseHelper(object):
    @staticmethod
    def get(path, source):
        """
        Provides the ability to traverse a data source made up of any
        combination of lists and dicts.  Has simple rules for selecting item of
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
        if path.startswith('/'):
            path = path[1:]

        queue = deque(path.split('/'))
        obj = source

        while len(queue):
            path = queue.popleft()

            if isinstance(obj, types.ListType):
                filtered = filter(lambda i: 'id' in i and i['id'] == path, obj)
                obj = filtered[0] if filtered else None
            elif isinstance(obj, types.DictionaryType):
                obj = obj[path] if path else obj
            else:
                raise ValueError('Object or path is malformed')

        return obj

    @staticmethod
    def update(path, value, source):
        """
        Updates value selected with specified path.

        Warning: Root object could not be updated

        :param path: string with path to desired value
        :param value: value
        :param source: python object (list or dict)
        """
        parent_path = '/'.join(path.split('/')[:-1])
        node = TraverseHelper.get(parent_path, source)
        key = path[1:].split('/')[-1]
        node[key] = value

    @staticmethod
    def insert(path, value, source):
        """
        Inserts new item to selected list.

        :param path: string with path to desired value
        :param value: value
        :param source: python object (list or dict)
        """
        node = TraverseHelper.get(path, source)
        node.append(value)


def auto_id(value):
    if isinstance(value, types.DictionaryType):
        value['id'] = generate_uuid()
        for k, v in value.iteritems():
            value[k] = auto_id(v)
    if isinstance(value, types.ListType):
        for item in value:
            auto_id(item)
    return value


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    """

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            forever = mtries == -1
            while forever or mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:

                    log.exception(e)
                    log.info("Retrying in {0} seconds...".format(mdelay))

                    eventlet.sleep(mdelay)

                    if not forever:
                        mtries -= 1

                    if mdelay < 60:
                        mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry

    return deco_retry


def handle(f):
    """Handles exception in wrapped function and writes to log."""

    @wraps(f)
    def f_handle(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            log.exception(e)

    return f_handle


def validate_body(schema):
    def deco_validate_body(f):
        @wraps(f)
        def f_validate_body(*args, **kwargs):
            if 'body' in kwargs:
                validate(kwargs['body'], schema)
                return f(*args, **kwargs)
        return f_validate_body
    return deco_validate_body
