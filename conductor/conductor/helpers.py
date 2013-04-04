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

import types


def transform_json(json, mappings):
    if isinstance(json, types.ListType):
        return [transform_json(t, mappings) for t in json]

    if isinstance(json, types.DictionaryType):
        result = {}
        for key, value in json.items():
            result[transform_json(key, mappings)] = \
                transform_json(value, mappings)
        return result

    if isinstance(json, types.StringTypes) and json.startswith('$'):
        value = mappings.get(json[1:])
        if value is not None:
            return value

    return json


def merge_dicts(dict1, dict2, max_levels=0):
    result = {}
    for key, value in dict1.items():
        result[key] = value
        if key in dict2:
            other_value = dict2[key]
            if max_levels == 1 or not isinstance(
                    other_value, types.DictionaryType):
                result[key] = other_value
            else:
                result[key] = merge_dicts(
                    value, other_value,
                    0 if max_levels == 0 else max_levels - 1)
    for key, value in dict2.items():
        if key not in result:
            result[key] = value
    return result


def find(f, seq):
    """Return first item in sequence where f(item) == True."""
    index = 0
    for item in seq:
        if f(item):
            return item, index
        index += 1
    return None, -1
