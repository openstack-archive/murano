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
import jsonschema
import tempfile

from oslo.config import cfg
from sqlalchemy import exc as sql_exc
from webob import exc

import muranoapi.api.v1
from muranoapi.api.v1 import schemas
from muranoapi.db.catalog import api as db_api
from muranoapi.openstack.common import exception
from muranoapi.openstack.common.gettextutils import _  # noqa
from muranoapi.openstack.common import log as logging
from muranoapi.openstack.common import wsgi
from muranoapi.packages import application_package as app_pkg
from muranoapi.packages import exceptions as pkg_exc

LOG = logging.getLogger(__name__)
CONF = cfg.CONF

SUPPORTED_PARAMS = muranoapi.api.v1.SUPPORTED_PARAMS
LIST_PARAMS = muranoapi.api.v1.LIST_PARAMS
ORDER_VALUES = muranoapi.api.v1.ORDER_VALUES
PKG_PARAMS_MAP = muranoapi.api.v1.PKG_PARAMS_MAP


def _check_content_type(req, content_type):
    try:
        req.get_content_type((content_type,))
    except exception.InvalidContentType:
        msg = _("Content-Type must be '{0}'").format(content_type)
        LOG.debug(msg)
        raise exc.HTTPBadRequest(explanation=msg)


def _get_filters(query_params):
    filters = {}
    for param_pair in query_params:
        k, v = param_pair
        if k not in SUPPORTED_PARAMS:
            LOG.warning(_("Search by parameter '{name}' "
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
                LOG.warning(_("Value of 'order_by' parameter is not valid. "
                              "Allowed values are: {0}. Skipping it.").format(
                            ", ".join(ORDER_VALUES)))
    return filters


def _validate_body(body):
    if len(body.keys()) != 2:
        msg = "multipart/form-data request should contain " \
              "two parts: json and tar.gz archive"
        LOG.error(msg)
        raise exc.HTTPBadRequest(msg)
    file_obj = None
    package_meta = None
    for part in body.values():
        if isinstance(part, cgi.FieldStorage):
            file_obj = part
            # dict if json deserialized successfully
        if isinstance(part, dict):
            package_meta = part
    if file_obj is None:
        msg = _("There is no file package with application description")
        LOG.error(msg)
        raise exc.HTTPBadRequest(msg)
    if package_meta is None:
        msg = _("There is no json with meta information about package")
        LOG.error(msg)
        raise exc.HTTPBadRequest(msg)
    return file_obj, package_meta


class Controller(object):
    """
        WSGI controller for application catalog resource in Murano v1 API
    """

    def update(self, req, body, package_id):
        """
        List of allowed changes:
            { "op": "add", "path": "/tags", "value": [ "foo", "bar" ] }
            { "op": "add", "path": "/categories", "value": [ "foo", "bar" ] }
            { "op": "remove", "path": "/tags" }
            { "op": "replace", "path": "/tags", "value": ["foo", "bar"] }
            { "op": "replace", "path": "/is_public", "value": true }
            { "op": "replace", "path": "/description",
                                "value":"New description" }
            { "op": "replace", "path": "/name", "value": "New name" }
        """
        _check_content_type(req, 'application/murano-packages-json-patch')
        if not isinstance(body, list):
            msg = _('Request body must be a JSON array of operation objects.')
            LOG.error(msg)
            raise exc.HTTPBadRequest(explanation=msg)
        package = db_api.package_update(package_id, body, req.context)

        return package.to_dict()

    def get(self, req, package_id):
        package = db_api.package_get(package_id, req.context)
        return package.to_dict()

    def search(self, req):
        filters = _get_filters(req.GET._items)
        packages = db_api.package_search(filters, req.context)
        return {"packages": [package.to_dict() for package in packages]}

    def upload(self, req, body=None):
        """
        Upload new file archive for the new package
        together with package metadata
        """
        _check_content_type(req, 'multipart/form-data')
        file_obj, package_meta = _validate_body(body)
        try:
            jsonschema.validate(package_meta, schemas.PKG_UPLOAD_SCHEMA)
        except jsonschema.ValidationError as e:
            LOG.exception(e)
            raise exc.HTTPBadRequest(explanation=e.message)

        with tempfile.NamedTemporaryFile() as tempf:
            content = file_obj.file.read()
            if not content:
                msg = _("Uploading file can't be empty")
                raise exc.HTTPBadRequest(msg)
            tempf.write(content)
            package_meta['archive'] = content
            try:
                pkg_to_upload = app_pkg.load_from_file(tempf.name,
                                                       target_dir=None,
                                                       drop_dir=True)
            except pkg_exc.PackageLoadError as e:
                LOG.exception(e)
                raise exc.HTTPBadRequest(e.message)

        # extend dictionary for update db
        for k, v in PKG_PARAMS_MAP.iteritems():
            if hasattr(pkg_to_upload, k):
                package_meta[v] = getattr(pkg_to_upload, k)
        try:
            package = db_api.package_upload(package_meta, req.context.tenant)
        except sql_exc.SQLAlchemyError:
            msg = _('Unable to save package in database')
            LOG.exception(msg)
            raise exc.HTTPServerError(msg)
        return package.to_dict()

    def get_ui(self, req, package_id):
        package = db_api.package_get(package_id, req.context)
        return package.ui_definition

    def get_logo(self, req, package_id):
        package = db_api.package_get(package_id, req.context)
        return package.logo

    def download(self, req, package_id):
        package = db_api.package_get(package_id, req.context)
        return package.archive

    def delete(self, req, package_id):
        db_api.package_delete(package_id)

    def show_categories(self, req):
        categories = db_api.categories_list()
        return {"categories": [category.to_dict() for category in categories]}


class PackageSerializer(wsgi.ResponseSerializer):
    def serialize(self, action_result, accept, action):
        if action == 'get_ui':
            accept = 'text/plain'
        elif action in ('download', 'get_logo'):
            accept = 'application/octet-stream'
        return super(PackageSerializer, self).serialize(action_result,
                                                        accept,
                                                        action)


def create_resource():
    serializer = PackageSerializer()
    return wsgi.Resource(Controller(), serializer=serializer)
