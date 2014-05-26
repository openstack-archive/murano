# Copyright (c) 2014 Mirantis Inc.
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

import inspect
import json
import logging
import os
import yaml

import nose
import unittest2 as unittest

from murano.common import uuidutils
from murano.dsl import executor
from murano.dsl import murano_class
from murano.dsl import namespace_resolver
from murano.engine import simple_cloader
from murano.engine.system import system_objects


LOG = logging.getLogger('nose.plugins.munit')


@murano_class.classname('io.murano.language.tests.TestCase')
class BaseTestCase(object):
    pass


class ManifestClassLoader(simple_cloader.SimpleClassLoader):
    def __init__(self, base_loader, base_path):
        self._base_loader = base_loader
        super(ManifestClassLoader, self).__init__(base_path)

    def load_definition(self, name):
        manifest_file = os.path.join(self._base_path, 'manifest.yaml')
        if not os.path.exists(manifest_file):
            return None

        with open(manifest_file) as stream:
            manifest = yaml.load(stream)
        pkg_classes = manifest.get('Classes', {})

        if name in pkg_classes:
            class_file = os.path.join(self._base_path, pkg_classes[name])
            with open(class_file) as stream:
                return yaml.load(stream)
        else:
            return self._base_loader.load_definition(name)


class MUnitTestCase(unittest.TestCase):
    def __init__(self, loader, test_case, case_name):
        self._executor = executor.MuranoDslExecutor(loader)
        self._test_case = self._executor.load(test_case)
        self._case_name = case_name
        self.register_asserts()
        super(MUnitTestCase, self).__init__(methodName='runTest')

    def register_asserts(self):
        for item in dir(self):
            method = getattr(self, item)
            if ((inspect.ismethod(method) or inspect.isfunction(method))
                    and item.startswith('assert')):
                self._test_case.type.add_method(item, method)

    def runTest(self):
        self._test_case.type.invoke(self._case_name, self._executor,
                                    self._test_case, {})

    def __repr__(self):
        return "{0} ({1})".format(self._case_name, self._test_case.type.name)

    __str__ = __repr__


class MuranoPLUnitTestPlugin(nose.plugins.Plugin):
    name = 'munit'

    def options(self, parser, env=os.environ):
        parser.add_option('--metadata-dir')
        super(MuranoPLUnitTestPlugin, self).options(parser, env=env)

    def configure(self, options, conf):
        self._metadata_dir = options.metadata_dir
        super(MuranoPLUnitTestPlugin, self).configure(options, conf)

    def loadTestsFromFile(self, filename):
        with open(filename) as stream:
            manifest = yaml.load(stream)
        pkg_directory = os.path.dirname(filename)

        base_cloader = simple_cloader.SimpleClassLoader(self._metadata_dir)
        cloader = ManifestClassLoader(base_cloader, pkg_directory)
        system_objects.register(cloader, pkg_directory)
        cloader.import_class(BaseTestCase)

        package_classes = manifest.get('Classes', {})
        for class_name, class_file in package_classes.iteritems():
            class_file = os.path.join(pkg_directory, class_file)
            with open(class_file) as stream:
                class_definition = yaml.load(stream)

            if not self._is_test_suite(class_definition):
                yield None

            test_object = self._get_test_object(class_name, class_file)

            test_cases = class_definition.get('Workflow', {})
            for case_name, _ in test_cases.iteritems():
                yield MUnitTestCase(cloader, test_object, case_name)

        yield None

    @staticmethod
    def _get_test_object(class_name, class_file):
        class_file = os.path.abspath(class_file)

        extension_length = os.path.splitext(class_file)
        object_file = class_file[:-len(extension_length)] + 'json'

        if os.path.exists(object_file):
            with open(object_file) as stream:
                return json.load(stream)
        else:
            return {
                "Objects": {
                    "?": {
                        "id": uuidutils.generate_uuid(),
                        "type": class_name
                    }
                }
            }

    @staticmethod
    def _is_test_suite(class_definition):
        namespaces = class_definition.get('Namespaces', {})
        extends = class_definition.get('Extends')

        ns_resolver = namespace_resolver.NamespaceResolver(namespaces)
        parent_name = ns_resolver.resolve_name(extends)

        return parent_name == 'io.murano.language.tests.TestCase'

    def wantFile(self, file):
        if file.endswith('manifest.yaml'):
            return True
