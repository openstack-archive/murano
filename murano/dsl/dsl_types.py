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

import weakref


class ClassUsages(object):
    Class = 'Class'
    Meta = 'Meta'
    All = {Class, Meta}


class MetaCardinality(object):
    One = 'One'
    Many = 'Many'
    All = {One, Many}


class MetaTargets(object):
    Package = 'Package'
    Type = 'Type'
    Property = 'Property'
    Method = 'Method'
    Argument = 'Argument'
    All = {Package, Type, Property, Method, Argument}


class PropertyUsages(object):
    In = 'In'
    Out = 'Out'
    InOut = 'InOut'
    Runtime = 'Runtime'
    Const = 'Const'
    Config = 'Config'
    Static = 'Static'
    All = {In, Out, InOut, Runtime, Const, Config, Static}
    Writable = {Out, InOut, Runtime, Static, Config}


class MethodUsages(object):
    Action = 'Action'
    Runtime = 'Runtime'
    Static = 'Static'
    Extension = 'Extension'

    All = {Action, Runtime, Static, Extension}
    InstanceMethods = {Runtime, Action}
    StaticMethods = {Static, Extension}


class MethodScopes(object):
    Session = 'Session'
    Public = 'Public'

    All = {Session, Public}


class MethodArgumentUsages(object):
    Standard = 'Standard'
    VarArgs = 'VarArgs'
    KwArgs = 'KwArgs'
    All = {Standard, VarArgs, KwArgs}


class DumpTypes(object):
    Serializable = 'Serializable'
    Inline = 'Inline'
    Mixed = 'Mixed'
    All = {Serializable, Inline, Mixed}


class MuranoType(object):
    pass


class MuranoClass(MuranoType):
    pass


class MuranoMetaClass(MuranoClass):
    pass


class MuranoObject(object):
    pass


class MuranoMethod(object):
    pass


class MuranoMethodArgument(object):
    pass


class MuranoPackage(object):
    pass


class MuranoProperty(object):
    pass


class MuranoTypeReference(object):
    def __init__(self, murano_type):
        self.__murano_type = weakref.ref(murano_type)

    @property
    def type(self):
        return self.__murano_type()

    def __repr__(self):
        return '*' + repr(self.type)

    def __eq__(self, other):
        if not isinstance(other, MuranoTypeReference):
            return False
        return self.type == other.type

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.type)


class YaqlExpression(object):
    pass


class MuranoObjectInterface(object):
    pass


class ExpressionFilePosition(object):
    def __init__(self, file_path, start_line, start_column,
                 end_line, end_column):
        self._file_path = file_path
        self._start_line = start_line
        self._start_column = start_column
        self._end_line = end_line
        self._end_column = end_column

    @property
    def file_path(self):
        return self._file_path

    @property
    def start_line(self):
        return self._start_line

    @property
    def start_column(self):
        return self._start_column

    @property
    def end_line(self):
        return self._end_line

    @property
    def end_column(self):
        return self._end_column
