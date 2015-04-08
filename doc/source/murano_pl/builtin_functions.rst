..
      Copyright 2014 Mirantis, Inc.

      Licensed under the Apache License, Version 2.0 (the "License"); you may
      not use this file except in compliance with the License. You may obtain
      a copy of the License at

          http://www.apache.org/licenses/LICENSE-2.0

      Unless required by applicable law or agreed to in writing, software
      distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
      WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
      License for the specific language governing permissions and limitations
      under the License.


==================
Built-In functions
==================

Murano has built-in functions which allows to do basic operations
with Murano PL objects.

List operations
====================

**list.skip(count)**

This function returns a sliced subset of initial list. It is equal
to Python a[count:] function.

**list.take(count)**

Returns first "count" elements of a list. IT is equal to a[:count]
operation in Python.
