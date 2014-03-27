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

from oslo.config import cfg
from webob import exc

import muranoapi.api.v1
from muranoapi.db.catalog import api as db_api
from muranoapi.openstack.common import exception
from muranoapi.openstack.common.gettextutils import _  # noqa
from muranoapi.openstack.common import log as logging
from muranoapi.openstack.common import wsgi


LOG = logging.getLogger(__name__)
CONF = cfg.CONF

SUPPORTED_PARAMS = muranoapi.api.v1.SUPPORTED_PARAMS
LIST_PARAMS = muranoapi.api.v1.LIST_PARAMS
ORDER_VALUES = muranoapi.api.v1.ORDER_VALUES


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


def create_resource():
    return wsgi.Resource(Controller())
