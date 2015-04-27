#    Copyright (c) 2014 Mirantis, Inc.
#
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

import cgi
import os
import tempfile

import jsonschema
from oslo.config import cfg
from oslo.db import exception as db_exc
from webob import exc

import murano.api.v1
from murano.api.v1 import schemas
from murano.common import policy
from murano.common import wsgi
from murano.db.catalog import api as db_api
from murano.common.i18n import _, _LW
from murano.openstack.common import exception
from murano.openstack.common import log as logging
from murano.packages import exceptions as pkg_exc
from murano.packages import load_utils


LOG = logging.getLogger(__name__)
CONF = cfg.CONF

SUPPORTED_PARAMS = murano.api.v1.SUPPORTED_PARAMS
LIST_PARAMS = murano.api.v1.LIST_PARAMS
ORDER_VALUES = murano.api.v1.ORDER_VALUES
PKG_PARAMS_MAP = murano.api.v1.PKG_PARAMS_MAP


def _check_content_type(req, content_type):
    try:
        req.get_content_type((content_type,))
    except exception.InvalidContentType:
        msg = _("Content-Type must be '{0}'").format(content_type)
        LOG.error(msg)
        raise exc.HTTPBadRequest(explanation=msg)


def _get_filters(query_params):
    filters = {}
    for param_pair in query_params:
        k, v = param_pair
        if k not in SUPPORTED_PARAMS:
            LOG.warning(_LW("Search by parameter '{name}' "
                            "is not supported. Skipping it.").format(name=k))
            continue

        if k in LIST_PARAMS:
            filters.setdefault(k, []).append(v)
        else:
            filters[k] = v
        order_by = filters.get('order_by', [])
        for i in order_by[:]:
            if ORDER_VALUES and i not in ORDER_VALUES:
                filters['order_by'].remove(i)
                LOG.warning(_LW(
                    "Value of 'order_by' parameter is not valid. "
                    "Allowed values are: {0}. Skipping it.").format(
                    ", ".join(ORDER_VALUES)))
    return filters


def _validate_body(body):
    """Check multipart/form-data has two parts: text (which is json string and
       should parsed into dictionary in serializer) and file, which stores as
       cgi.FieldStorage instance. Also validate file size doesn't exceed
       the limit: seek to the end of the file, get the position of EOF and
       reset the file position to the beginning
    """
    def check_file_size(f):
        mb_limit = CONF.packages_opts.package_size_limit
        pkg_size_limit = mb_limit * 1024 * 1024
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > pkg_size_limit:
            raise exc.HTTPBadRequest(explanation=_(
                'Uploading file is too large.'
                ' The limit is {0} Mb').format(mb_limit))

    if len(body.keys()) > 2:
        msg = _("'multipart/form-data' request body should contain "
                "1 or 2 parts: json string and zip archive. Current body "
                "consists of {0} part(s)").format(len(body.keys()))
        LOG.error(msg)
        raise exc.HTTPBadRequest(explanation=msg)

    file_obj = None
    package_meta = None
    for part in body.values():
        if isinstance(part, cgi.FieldStorage):
            file_obj = part
            check_file_size(file_obj.file)

        if isinstance(part, dict):
            package_meta = part
    if file_obj is None:
        msg = _('There is no file package with application description')
        LOG.error(msg)
        raise exc.HTTPBadRequest(explanation=msg)
    return file_obj, package_meta


class Controller(object):
    """WSGI controller for application catalog resource in Murano v1 API."""

    def update(self, req, body, package_id):
        """List of allowed changes:
            { "op": "add", "path": "/tags", "value": [ "foo", "bar" ] }
            { "op": "add", "path": "/categories", "value": [ "foo", "bar" ] }
            { "op": "remove", "path": "/tags" }
            { "op": "remove", "path": "/categories" }
            { "op": "replace", "path": "/tags", "value": ["foo", "bar"] }
            { "op": "replace", "path": "/is_public", "value": true }
            { "op": "replace", "path": "/description",
                                "value":"New description" }
            { "op": "replace", "path": "/name", "value": "New name" }
        """
        policy.check("modify_package", req.context, {'package_id': package_id})

        pkg_to_update = db_api.package_get(package_id, req.context)
        if pkg_to_update.is_public:
            policy.check("manage_public_package", req.context)

        _check_content_type(req, 'application/murano-packages-json-patch')
        if not isinstance(body, list):
            msg = _('Request body must be a JSON array of operation objects.')
            LOG.error(msg)
            raise exc.HTTPBadRequest(explanation=msg)
        for change in body:
            if 'is_public' in change['path']:
                if change['value'] is True and not pkg_to_update.is_public:
                    policy.check('publicize_package', req.context)
                break
        package = db_api.package_update(package_id, body, req.context)
        return package.to_dict()

    def get(self, req, package_id):
        policy.check("get_package", req.context, {'package_id': package_id})

        package = db_api.package_get(package_id, req.context)
        return package.to_dict()

    def search(self, req):
        def _validate_limit(value):
            if value is None:
                return
            try:
                value = int(value)
            except ValueError:
                msg = _("limit param must be an integer")
                LOG.error(msg)
                raise exc.HTTPBadRequest(explanation=msg)

            if value <= 0:
                msg = _("limit param must be positive")
                LOG.error(msg)
                raise exc.HTTPBadRequest(explanation=msg)

            return value

        policy.check("get_package", req.context)

        filters = _get_filters(req.GET.items())

        limit = _validate_limit(filters.get('limit'))
        if limit is None:
            limit = CONF.packages_opts.limit_param_default
        limit = min(CONF.packages_opts.api_limit_max, limit)

        result = {}

        catalog = req.GET.pop('catalog', '').lower() == 'true'
        packages = db_api.package_search(
            filters, req.context, limit, catalog=catalog)
        if len(packages) == limit:
            result['next_marker'] = packages[-1].id
        result['packages'] = [package.to_dict() for package in packages]
        return result

    def upload(self, req, body=None):
        """Upload new file archive for the new package
           together with package metadata.
        """
        policy.check("upload_package", req.context)

        _check_content_type(req, 'multipart/form-data')
        file_obj, package_meta = _validate_body(body)
        if package_meta:
            try:
                jsonschema.validate(package_meta, schemas.PKG_UPLOAD_SCHEMA)
            except jsonschema.ValidationError as e:
                msg = _("Package schema is not valid: {0}").format(e)
                LOG.exception(msg)
                raise exc.HTTPBadRequest(explanation=msg)
        else:
            package_meta = {}

        if package_meta.get('is_public'):
            policy.check('publicize_package', req.context)

        with tempfile.NamedTemporaryFile(delete=False) as tempf:
            LOG.debug("Storing package archive in a temporary file")
            content = file_obj.file.read()
            if not content:
                msg = _("Uploading file can't be empty")
                LOG.error(msg)
                raise exc.HTTPBadRequest(explanation=msg)
            tempf.write(content)
            package_meta['archive'] = content
        try:
            pkg_to_upload = load_utils.load_from_file(
                tempf.name, target_dir=None, drop_dir=True)
        except pkg_exc.PackageLoadError as e:
            msg = _("Couldn't load package from file: {0}").format(e)
            LOG.exception(msg)
            raise exc.HTTPBadRequest(explanation=msg)
        finally:
            LOG.debug("Deleting package archive temporary file")
            os.remove(tempf.name)

        # extend dictionary for update db
        for k, v in PKG_PARAMS_MAP.iteritems():
            if hasattr(pkg_to_upload, k):
                package_meta[v] = getattr(pkg_to_upload, k)

        try:
            package = db_api.package_upload(package_meta, req.context.tenant)
        except db_exc.DBDuplicateEntry:
            msg = _('Package with specified full name is already registered')
            LOG.exception(msg)
            raise exc.HTTPConflict(msg)
        return package.to_dict()

    def get_ui(self, req, package_id):
        target = {'package_id': package_id}
        policy.check("get_package", req.context, target)

        package = db_api.package_get(package_id, req.context)
        return package.ui_definition

    def get_logo(self, req, package_id):
        target = {'package_id': package_id}
        policy.check("get_package", req.context, target)

        package = db_api.package_get(package_id, req.context)
        return package.logo

    def get_supplier_logo(self, req, package_id):
        package = db_api.package_get(package_id, req.context)
        return package.supplier_logo

    def download(self, req, package_id):
        target = {'package_id': package_id}
        policy.check("download_package", req.context, target)

        package = db_api.package_get(package_id, req.context)
        return package.archive

    def delete(self, req, package_id):
        target = {'package_id': package_id}
        policy.check("delete_package", req.context, target)

        package = db_api.package_get(package_id, req.context)
        if package.is_public:
            policy.check("manage_public_package", req.context, target)
        db_api.package_delete(package_id, req.context)

    def get_category(self, req, category_id):
        policy.check("get_category", req.context)
        category = db_api.category_get(category_id, packages=True)
        return category.to_dict()

    def show_categories(self, req):
        policy.check("get_category", req.context)
        categories = db_api.categories_list()
        return {'categories': [category.name for category in categories]}

    def list_categories(self, req):
        policy.check("get_category", req.context)
        categories = db_api.categories_list()
        return {'categories': [category.to_dict() for category in categories]}

    def add_category(self, req, body=None):
        policy.check("add_category", req.context)

        if not body.get('name'):
            raise exc.HTTPBadRequest(
                explanation='Please, specify a name of the category to create')
        try:
            category = db_api.category_add(body['name'])
        except db_exc.DBDuplicateEntry:
            msg = _('Category with specified name is already exist')
            LOG.error(msg)
            raise exc.HTTPConflict(explanation=msg)
        return category.to_dict()

    def delete_category(self, req, category_id):
        target = {'category_id': category_id}
        policy.check("delete_category", req.context, target)
        category = db_api.category_get(category_id, packages=True)
        if category.packages:
            msg = _("It's impossible to delete categories assigned"
                    " to the package, uploaded to the catalog")
            raise exc.HTTPForbidden(explanation=msg)
        db_api.category_delete(category_id)


class PackageSerializer(wsgi.ResponseSerializer):
    def serialize(self, action_result, accept, action):
        if action == 'get_ui':
            accept = 'text/plain'
        elif action in ('download', 'get_logo', 'get_supplier_logo'):
            accept = 'application/octet-stream'
        return super(PackageSerializer, self).serialize(action_result,
                                                        accept,
                                                        action)


def create_resource():
    serializer = PackageSerializer()
    return wsgi.Resource(Controller(), serializer=serializer)
