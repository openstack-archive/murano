#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import mock
from oslo_config import cfg

from murano.common import plugin_loader
from murano.tests.unit import base

CONF = cfg.CONF


class PluginLoaderTest(base.MuranoTestCase):

    def setUp(self):
        super(PluginLoaderTest, self).setUp()

    @mock.patch('stevedore.extension.Extension')
    def test_load_extension(self, ext):
        """Test PluginLoader.load_extension.
        Check that stevedore plugin loading creates instance
        of PackageDefinition class, new class are added to that package
        and name mapping between class and plugin are updated.
        """
        ext.entry_point.dist.project_name = 'plugin1'
        ext.entry_point.name = 'Test'

        name_map = {}
        test_obj = plugin_loader.PluginLoader('test.namespace')
        test_obj.load_extension(ext, name_map)
        self.assertEqual(1, len(test_obj.packages))
        loaded_pkg = test_obj.packages.values()[0]
        self.assertTrue(isinstance(loaded_pkg,
                                   plugin_loader.PackageDefinition))
        self.assertEqual('test.namespace.Test', loaded_pkg.classes.keys()[0])
        self.assertEqual({'test.namespace.Test': test_obj.packages.keys()},
                         name_map)

    def test_cleanup_duplicates(self):
        """Test PluginLoader.cleanup_duplicates.
        Check loading two plugins with same 'Test1' classes
        inside initiates removing of all duplicated classes.
        """
        name_map = {}
        ext1 = mock.MagicMock(name='ext1')
        ext1.entry_point.name = 'Test1'
        ext2 = mock.MagicMock(name='ext2')
        ext2.entry_point.name = 'Test1'

        test_obj = plugin_loader.PluginLoader()
        test_obj.load_extension(ext1, name_map)
        test_obj.load_extension(ext2, name_map)

        dist1 = ext1.entry_point.dist
        dist2 = ext2.entry_point.dist
        self.assertEqual(1, len(test_obj.packages[str(dist1)].classes))
        self.assertEqual(1, len(test_obj.packages[str(dist2)].classes))
        test_obj.cleanup_duplicates(name_map)

        self.assertEqual(0, len(test_obj.packages[str(dist1)].classes))
        self.assertEqual(0, len(test_obj.packages[str(dist2)].classes))

    def test_load_plugin_with_inappropriate_class_name(self):
        """Negative test load_extension.
        Check plugin that contains incorrect MuranoPL class name
        won't be loaded.
        """
        name_map = {}
        ext = mock.MagicMock(name='ext')
        ext.entry_point.name = 'murano-pl-class'

        test_obj = plugin_loader.PluginLoader()
        test_obj.load_extension(ext, name_map)
        # No packages are loaded
        self.assertEqual(0, len(test_obj.packages))

    @mock.patch('stevedore.extension.Extension')
    def test_is_plugin_enabled(self, ext):
        """Test is_plugin_enabled.
        Check that only plugins specified in config file can be loaded.
        """
        self.override_config('enabled_plugins',
                             'plugin1, plugin2',
                             group='murano')
        ext.entry_point.dist.project_name = 'test'
        test_method = plugin_loader.PluginLoader.is_plugin_enabled
        self.assertFalse(test_method(ext))
        ext.entry_point.dist.project_name = 'plugin1'
        self.assertTrue(test_method(ext))
