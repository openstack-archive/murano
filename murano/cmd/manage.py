#    Copyright (c) 2014 Mirantis, Inc.
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

"""
  *** Deprecation warning ***
  This file is about to be deprecated, please use python-muranoclient.
  *** Deprecation warning ***
"""

import sys
import traceback

from oslo.config import cfg
from oslo.db import exception as db_exception

from murano.common import consts
from murano.db.catalog import api as db_catalog_api
from murano.common.i18n import _LI, _LE
from murano.openstack.common import log as logging
from murano.packages import load_utils
from murano import version

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class AdminContext(object):
    def __init__(self):
        self.is_admin = True


def _do_import_package(_dir, categories, update=False):
    LOG.info(_LI("Going to import Murano package from {0}").format(_dir))
    pkg = load_utils.load_from_dir(_dir)

    LOG.info(_LI("Checking for existing"))
    existing = db_catalog_api.package_search(
        {'fqn': pkg.full_name},
        AdminContext())
    if existing:
        existing_pkg = existing[0]
        if update:
            LOG.info(_LI(
                "Deleting existing package {0}").format(existing_pkg.id))
            db_catalog_api.package_delete(existing_pkg.id, AdminContext())
        else:
            LOG.error(_LE("Package '{0}' exists ({1}). Use --update.").format(
                pkg.full_name,
                existing_pkg.id))
            return

    package = {
        'fully_qualified_name': pkg.full_name,
        'type': pkg.package_type,
        'author': pkg.author,
        'supplier': pkg.supplier,
        'name': pkg.display_name,
        'description': pkg.description,
        # note: we explicitly mark all the imported packages as public,
        # until a parameter added to control visibility scope of a package
        'is_public': True,
        'tags': pkg.tags,
        'logo': pkg.logo,
        'supplier_logo': pkg.supplier_logo,
        'ui_definition': pkg.raw_ui,
        'class_definitions': pkg.classes,
        'archive': pkg.blob,
        'categories': categories or []
    }

    # note(ruhe): the second parameter is tenant_id
    # it is a required field in the DB, that's why we pass an empty string
    result = db_catalog_api.package_upload(package, '')

    LOG.info(_LI("Finished import of package {0}").format(result.id))


# TODO(ruhe): proper error handling
def do_import_package():
    """Import Murano package from local directory."""
    _do_import_package(
        CONF.command.directory,
        CONF.command.categories,
        CONF.command.update)


def do_list_categories():
    categories = db_catalog_api.category_get_names()

    if categories:
        print(">> Murano package categories:")
        for c in categories:
            print("* {0}".format(c))
    else:
        print("No categories were found")


def do_add_category():
    category_name = CONF.command.category_name

    try:
        db_catalog_api.category_add(category_name)
        print(">> Successfully added category {0}".format(category_name))
    except db_exception.DBDuplicateEntry:
        print(">> ERROR: Category '{0}' already exists".format(category_name))


def add_command_parsers(subparsers):
    parser = subparsers.add_parser('import-package')
    parser.set_defaults(func=do_import_package)
    parser.add_argument('directory',
                        help='A directory with Murano package.')
    parser.add_argument('-u', '--update',
                        action="store_true",
                        default=False,
                        help='If a package already exists, delete and update')
    parser.add_argument('-c', '--categories',
                        choices=consts.CATEGORIES,
                        nargs='*',
                        help='An optional list of categories this package '
                             'to be assigned to.')

    parser = subparsers.add_parser('category-list')
    parser.set_defaults(func=do_list_categories)

    parser = subparsers.add_parser('category-add')
    parser.set_defaults(func=do_add_category)
    parser.add_argument('category_name',
                        help='Name of the new category.')


command_opt = cfg.SubCommandOpt('command',
                                title='Commands',
                                help='Show available commands.',
                                handler=add_command_parsers)


def main():
    CONF.register_cli_opt(command_opt)

    try:
        default_config_files = cfg.find_config_files('murano', 'murano')
        CONF(sys.argv[1:], project='murano', prog='murano-manage',
             version=version.version_string,
             default_config_files=default_config_files)
        logging.setup("murano")
    except RuntimeError as e:
        LOG.error(_LE("failed to initialize murano-manage: %s") % e)
        sys.exit("ERROR: %s" % e)

    try:
        CONF.command.func()
    except Exception as e:
        tb = traceback.format_exc()
        err_msg = _LE("murano-manage command failed: {0}\n{1}").format(e, tb)
        LOG.error(err_msg)
        sys.exit(err_msg)


if __name__ == '__main__':
    main()
