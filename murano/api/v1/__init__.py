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

stats = None

SUPPORTED_PARAMS = {'id', 'order_by', 'category', 'marker', 'tag',
                    'class_name', 'limit', 'type', 'fqn', 'category', 'owned',
                    'search', 'include_disabled', 'sort_dir', 'name'}
LIST_PARAMS = {'id', 'category', 'tag', 'class', 'order_by'}
ORDER_VALUES = {'fqn', 'name', 'created'}
OPERATOR_VALUES = {'id', 'category', 'tag'}
PKG_PARAMS_MAP = {'display_name': 'name',
                  'full_name': 'fully_qualified_name',
                  'ui': 'ui_definition',
                  'logo': 'logo',
                  'package_type': 'type',
                  'description': 'description',
                  'author': 'author',
                  'classes': 'class_definitions',
                  'tags': 'tags',
                  'supplier': 'supplier',
                  'supplier_logo': 'supplier_logo'}
