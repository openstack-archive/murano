#    Copyright (c) 2016 Mirantis, Inc.
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

# This code is almost a complete copy of eventlet.corolocal with only
# the concept of current thread replaced with current session

import weakref

import six

from murano.dsl import helpers


# the entire purpose of this class is to store off the constructor
# arguments in a local variable without calling __init__ directly
class _localbase(object):
    __slots__ = '_local__args', '_local__sessions'

    def __new__(cls, *args, **kw):
        self = object.__new__(cls)
        object.__setattr__(self, '_local__args', (args, kw))
        object.__setattr__(
            self, '_local__sessions', weakref.WeakKeyDictionary())
        if (args or kw) and (cls.__init__ is object.__init__):
            raise TypeError('Initialization arguments are not supported')
        return self


def _patch(session_local):
    sessions_dict = object.__getattribute__(session_local, '_local__sessions')
    session = helpers.get_execution_session()
    localdict = sessions_dict.get(session)
    if localdict is None:
        # must be the first time we've seen this session, call __init__
        localdict = {}
        sessions_dict[session] = localdict
        cls = type(session_local)
        if cls.__init__ is not object.__init__:
            args, kw = object.__getattribute__(session_local, '_local__args')
            session_local.__init__(*args, **kw)
    object.__setattr__(session_local, '__dict__', localdict)


class _local(_localbase):
    def __getattribute__(self, attr):
        _patch(self)
        return object.__getattribute__(self, attr)

    def __setattr__(self, attr, value):
        _patch(self)
        return object.__setattr__(self, attr, value)

    def __delattr__(self, attr):
        _patch(self)
        return object.__delattr__(self, attr)


def session_local(cls):
    return type(cls.__name__, (cls, _local), {})


class SessionLocalDict(six.moves.UserDict, object):
    def __init__(self, **kwargs):
        self.__session_data = weakref.WeakKeyDictionary()
        self.__default = {}
        super(SessionLocalDict, self).__init__(**kwargs)

    @property
    def data(self):
        session = helpers.get_execution_session()
        if session is None:
            return self.__default
        return self.__session_data.setdefault(session, {})

    @data.setter
    def data(self, value):
        session = helpers.get_execution_session()
        if session is None:
            self.__default = value
        else:
            self.__session_data[session] = value


def execution_session_memoize(func):
    cache = SessionLocalDict()
    return helpers.get_memoize_func(func, cache)
