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


class MuranoClass(object):
    pass


class MuranoObject(object):
    pass


class MuranoMethod(object):
    pass


class MuranoPackage(object):
    pass


class MuranoClassReference(object):
    def __init__(self, murano_class):
        self.__murano_class = murano_class

    @property
    def murano_class(self):
        return self.__murano_class

    def __str__(self):
        return self.__murano_class.name


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
