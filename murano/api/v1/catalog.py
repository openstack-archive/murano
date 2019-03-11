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
from keystoneclient import exceptions as keystone_ex
from keystoneclient import service_catalog
from oslo_config import cfg
from oslo_db import exception as db_exc
from oslo_log import log as logging
from webob import exc

import murano.api.v1
from murano.api.v1 import validation_schemas
from murano.common import exceptions
from murano.common.i18n import _
from murano.common import policy
import murano.common.utils as murano_utils
from murano.common import wsgi
from murano.db.catalog import api as db_api
from murano.packages import exceptions as pkg_exc
from murano.packages import load_utils
from muranoclient.glance import client as glare_client


LOG = logging.getLogger(__name__)
CONF = cfg.CONF

SUPPORTED_PARAMS = murano.api.v1.SUPPORTED_PARAMS
LIST_PARAMS = murano.api.v1.LIST_PARAMS
ORDER_VALUES = murano.api.v1.ORDER_VALUES
PKG_PARAMS_MAP = murano.api.v1.PKG_PARAMS_MAP
OPERATOR_VALUES = murano.api.v1.OPERATOR_VALUES


def _check_content_type(req, content_type):
    try:
        req.get_content_type((content_type,))
    except exceptions.UnsupportedContentType:
        msg = _("Content-Type must be '{type}'").format(type=content_type)
        LOG.error(msg)
        raise exc.HTTPBadRequest(explanation=msg)


def _get_filters(query_params):
    filters = {}
    for param_pair in query_params:
        k, v = param_pair
        if k not in SUPPORTED_PARAMS:
            LOG.warning("Search by parameter '{name}' "
                        "is not supported. Skipping it.".format(name=k))
            continue

        if k in LIST_PARAMS:
            if v.startswith('in:') and k in OPERATOR_VALUES:
                in_value = v[len('in:'):]
                try:
                    filters[k] = murano_utils.split_for_quotes(in_value)
                except ValueError as err:
                    LOG.warning("Search by parameter '{name}' "
                                "caused an {message} error."
                                "Skipping it.".format(name=k,
                                                      message=err))
            else:
                filters.setdefault(k, []).append(v)
        else:
            filters[k] = v
        order_by = filters.get('order_by', [])
        for i in order_by[:]:
            if ORDER_VALUES and i not in ORDER_VALUES:
                filters['order_by'].remove(i)
                LOG.warning("Value of 'order_by' parameter is not valid. "
                            "Allowed values are: {values}. Skipping it."
                            .format(values=", ".join(ORDER_VALUES)))
    return filters


def _validate_body(body):
    """Check multipart/form-data has two parts

    Check multipart/form-data has two parts: text (which is json string and
    should parsed into dictionary in serializer) and file, which stores as
    cgi.FieldStorage instance. Also validate file size doesn't exceed
    the limit: seek to the end of the file, get the position of EOF and
    reset the file position to the beginning
    """
    def check_file_size(f):
        mb_limit = CONF.murano.package_size_limit
        pkg_size_limit = mb_limit * 1024 * 1024
        f.seek(0, 2)
        size = f.tell()
        f.seek(0)
        if size > pkg_size_limit:
            raise exc.HTTPBadRequest(explanation=_(
                'Uploading file is too large. '
                'The limit is {0} Mb').format(mb_limit))

    if len(body) > 2:
        msg = _("'multipart/form-data' request body should contain 1 or 2 "
                "parts: json string and zip archive. Current body consists "
                "of {amount} part(s)").format(amount=len(body.keys()))
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

    def _validate_limit(self, value):
            if value is None:
                return
            try:
                value = int(value)
            except ValueError:
                msg = _("Limit param must be an integer")
                LOG.error(msg)
                raise exc.HTTPBadRequest(explanation=msg)

            if value <= 0:
                msg = _("Limit param must be positive")
                LOG.error(msg)
                raise exc.HTTPBadRequest(explanation=msg)

            return value

    def update(self, req, body, package_id):
        """List of allowed changes

        List of allowed changes:
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
            if 'name' in change['path']:
                if len(change['value']) > 80:
                    msg = _('Package name should be 80 characters maximum')
                    LOG.error(msg)
                    raise exc.HTTPBadRequest(explanation=msg)
        package = db_api.package_update(package_id, body, req.context)
        return package.to_dict()

    def get(self, req, package_id):
        policy.check("get_package", req.context, {'package_id': package_id})

        package = db_api.package_get(package_id, req.context)
        return package.to_dict()

    def search(self, req):
        policy.check("get_package", req.context)
        manage_public = True
        try:
            policy.check("manage_public_package", req.context)
        except exc.HTTPForbidden:
            manage_public = False

        filters = _get_filters(req.GET.items())

        limit = self._validate_limit(filters.get('limit'))
        if limit is None:
            limit = CONF.murano.limit_param_default
        limit = min(CONF.murano.api_limit_max, limit)

        result = {}

        catalog = req.GET.pop('catalog', '').lower() == 'true'
        packages = db_api.package_search(
            filters, req.context, manage_public, limit, catalog=catalog)
        if len(packages) == limit:
            result['next_marker'] = packages[-1].id
        result['packages'] = [package.to_dict() for package in packages]
        return result

    def upload(self, req, body=None):
        """Upload new file archive

        Upload new file archive for the new package
        together with package metadata.
        """
        policy.check("upload_package", req.context)

        _check_content_type(req, 'multipart/form-data')
        file_obj, package_meta = _validate_body(body)
        if package_meta:
            try:
                jsonschema.validate(package_meta,
                                    validation_schemas.PKG_UPLOAD_SCHEMA)
            except jsonschema.ValidationError as e:
                msg = _("Package schema is not valid: {reason}").format(
                    reason=e)
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
            with load_utils.load_from_file(
                    tempf.name, target_dir=None,
                    drop_dir=True) as pkg_to_upload:
                # extend dictionary for update db
                for k, v in PKG_PARAMS_MAP.items():
                    if hasattr(pkg_to_upload, k):
                        if k == "tags" and package_meta.get(k):
                            package_meta[v] = list(set(
                                package_meta[v] + getattr(pkg_to_upload, k)))
                        else:
                            package_meta[v] = getattr(pkg_to_upload, k)
                if len(package_meta['name']) > 80:
                    msg = _('Package name should be 80 characters maximum')
                    LOG.error(msg)
                    raise exc.HTTPBadRequest(explanation=msg)
                try:
                    package = db_api.package_upload(
                        package_meta, req.context.tenant)
                except db_exc.DBDuplicateEntry:
                    msg = _('Package with specified full '
                            'name is already registered')
                    LOG.exception(msg)
                    raise exc.HTTPConflict(msg)
                return package.to_dict()
        except pkg_exc.PackageLoadError as e:
            msg = _("Couldn't load package from file: {reason}").format(
                reason=e)
            LOG.exception(msg)
            raise exc.HTTPBadRequest(explanation=msg)
        finally:
            LOG.debug("Deleting package archive temporary file")
            os.remove(tempf.name)

    def get_ui(self, req, package_id):
        if CONF.engine.packages_service == 'murano':
            target = {'package_id': package_id}
            policy.check("get_package", req.context, target)

            package = db_api.package_get(package_id, req.context)
            return package.ui_definition
        else:
            g_client = self._get_glare_client(req)
            blob_data = g_client.artifacts.download_blob(package_id, 'archive')
            with tempfile.NamedTemporaryFile() as tempf:
                for chunk in blob_data:
                    tempf.write(chunk)
                tempf.file.flush()
                os.fsync(tempf.file.fileno())
                with load_utils.load_from_file(tempf.name, target_dir=None,
                                               drop_dir=True) as pkg:
                    return pkg.ui

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

    def list_categories(self, req):
        """List all categories

        List all categories with pagination and sorting
           Acceptable filter params:
           :param sort_keys: an array of fields used to sort the list
           :param sort_dir: the direction of the sort ('asc' or 'desc')
           :param limit: the number of categories to list
           :param marker: the ID of the last item in the previous page
        """
        def _get_category_filters(req):
            query_params = {}
            valid_query_params = ['sort_keys', 'sort_dir', 'limit', 'marker']
            for key, value in req.GET.items():
                if key not in valid_query_params:
                    raise exc.HTTPBadRequest(
                        _('Bad value passed to filter. '
                          'Got {key}, expected:{valid}').format(
                            key=key, valid=', '.join(valid_query_params)))
                if key == 'sort_keys':
                    available_sort_keys = ['name', 'created',
                                           'updated', 'package_count', 'id']
                    value = [v.strip() for v in value.split(',')]
                    for sort_key in value:
                        if sort_key not in available_sort_keys:
                            raise exc.HTTPBadRequest(
                                explanation=_('Invalid sort key: {sort_key}. '
                                              'Must be one of the following: '
                                              '{available}').format(
                                    sort_key=sort_key,
                                    available=', '.join(available_sort_keys)))
                if key == 'sort_dir':
                    if value not in ['asc', 'desc']:
                        msg = _('Invalid sort direction: {0}').format(value)
                        raise exc.HTTPBadRequest(explanation=msg)
                query_params[key] = value
            return query_params

        policy.check("get_category", req.context)

        filters = _get_category_filters(req)

        marker = filters.get('marker')
        limit = self._validate_limit(filters.get('limit'))

        result = {}
        categories = db_api.categories_list(filters,
                                            limit=limit,
                                            marker=marker)
        if len(categories) == limit:
            result['next_marker'] = categories[-1].id

        result['categories'] = [category.to_dict() for category in categories]
        return result

    def add_category(self, req, body=None):
        policy.check("add_category", req.context)
        category_name = body.get('name')
        if not category_name:
            raise exc.HTTPBadRequest(
                explanation='Please, specify a name of the category to create')
        if len(category_name) > 80:
            msg = _('Category name should be 80 characters maximum')
            LOG.error(msg)
            raise exc.HTTPBadRequest(explanation=msg)
        try:
            category = db_api.category_add(category_name)
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
            msg = _("It's impossible to delete categories assigned "
                    "to the package, uploaded to the catalog")
            raise exc.HTTPForbidden(explanation=msg)
        db_api.category_delete(category_id)

    def _get_glare_client(self, request):
        glare_settings = CONF.glare
        token = request.context.auth_token
        url = glare_settings.url
        if not url:
            url = self._get_glare_url(request)
        # TODO(gyurco): use auth_utils.get_session_client_parameters
        client = glare_client.Client(
            endpoint=url, token=token, insecure=glare_settings.insecure,
            key_file=glare_settings.keyfile or None,
            ca_file=glare_settings.cafile or None,
            cert_file=glare_settings.certfile or None,
            type_name='murano',
            type_version=1)
        return client

    def _get_glare_url(self, request):
        sc = request.context.service_catalog
        token = request.context.auth_token
        try:
            return service_catalog.ServiceCatalogV2(
                {'serviceCatalog': sc}).url_for(
                service_type='artifact',
                endpoint_type=CONF.glare.endpoint_type,
                region_name=CONF.home_region)
        except keystone_ex.EndpointNotFound:
            return service_catalog.ServiceCatalogV3(
                token,
                {'catalog': sc}).url_for(
                    service_type='artifact',
                    endpoint_type=CONF.glare.endpoint_type,
                    region_name=CONF.home_region)


def create_resource():
    specific_content_types = {
        'get_ui': ['text/plain'],
        'download': ['application/octet-stream'],
        'get_logo': ['application/octet-stream'],
        'get_supplier_logo': ['application/octet-stream']}
    deserializer = wsgi.RequestDeserializer(
        specific_content_types=specific_content_types)
    return wsgi.Resource(Controller(), deserializer=deserializer)
