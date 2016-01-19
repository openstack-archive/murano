# Copyright (c) 2015 Intel, Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import re

"""
Guidelines for writing new hacking checks
 - Use only for Murano specific tests. OpenStack general tests
   should be submitted to the common 'hacking' module.
 - Pick numbers in the range M3xx. Find the current test with
   the highest allocated number and then pick the next value.
   If nova has an N3xx code for that test, use the same number.
 - Keep the test method code in the source file ordered based
   on the M3xx value.
 - List the new rule in the top level HACKING.rst file
 - Add test cases for each new rule to /tests/unit/test_hacking.py
"""

mutable_default_args = re.compile(r"^\s*def .+\((.+=\{\}|.+=\[\])")


def no_mutable_default_args(logical_line):
    msg = "M322: Method's default argument shouldn't be mutable!"
    if mutable_default_args.match(logical_line):
        yield (0, msg)


def check_python3_no_iteritems(logical_line):
    if re.search(r".*\.iteritems\(\)", logical_line):
        msg = ("M323: Use six.iteritems() instead of dict.iteritems().")
        yield(0, msg)


def check_python3_no_iterkeys(logical_line):
    if re.search(r".*\.iterkeys\(\)", logical_line):
        msg = ("M324: Use six.iterkeys() instead of dict.iterkeys().")
        yield(0, msg)


def check_python3_no_itervalues(logical_line):
    if re.search(r".*\.itervalues\(\)", logical_line):
        msg = ("M325: Use six.itervalues() instead of dict.itervalues().")
        yield(0, msg)


def check_no_basestring(logical_line):
    if re.search(r"\bbasestring\b", logical_line):
        msg = ("M326: basestring is not Python3-compatible, use "
               "six.string_types instead.")
        yield(0, msg)


def factory(register):
    register(no_mutable_default_args)
    register(check_python3_no_iteritems)
    register(check_python3_no_iterkeys)
    register(check_python3_no_itervalues)
    register(check_no_basestring)
