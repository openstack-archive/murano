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

from sqlalchemy import or_
from sqlalchemy.orm import attributes
from sqlalchemy import sql
from webob import exc

from muranoapi.db import models
from muranoapi.db import session as db_session
from muranoapi.openstack.common.gettextutils import _  # noqa
from muranoapi.openstack.common import log as logging

SEARCH_MAPPING = {'fqn': 'fully_qualified_name',
                  'name': 'name',
                  'created': 'created'
                  }

LOG = logging.getLogger(__name__)


def _package_get(package_id, session):
    package = session.query(models.Package).get(package_id)
    if not package:
        msg = _("Package id '{0}' is not found").format(package_id)
        LOG.error(msg)
        raise exc.HTTPNotFound(msg)

    return package


def _authorize_package(package, context, allow_public=False):
    if context.is_admin:
        return

    if package.owner_id != context.tenant:
        if not allow_public:
            msg = _("Package '{0}' is not owned by "
                    "tenant '{1}'").format(package.id, context.tenant)
            LOG.error(msg)
            raise exc.HTTPForbidden(msg)
        if not package.is_public:
            msg = _("Package '{0}' is not public and not owned by "
                    "tenant '{1}' ").format(package.id, context.tenant)
            LOG.error(msg)
            raise exc.HTTPForbidden(msg)


def package_get(package_id, context):
    """
    Return package details
    :param package_id: ID of a package, string
    :returns: detailed information about package, dict
    """
    session = db_session.get_session()
    package = _package_get(package_id, session)
    _authorize_package(package, context, allow_public=True)
    return package


def _get_categories(category_names, session=None):
    """
    Return existing category objects or raise an exception
    :param category_names: name of categories to associate with package, list
    :returns: list of Category objects to associate with package, list
    """
    if session is None:
        session = db_session.get_session()
    categories = []
    for ctg_name in category_names:
        ctg_obj = session.query(models.Category).filter_by(
            name=ctg_name).first()
        if not ctg_obj:
            msg = _("Category '{name}' doesn't exist").format(name=ctg_name)
            LOG.error(msg)
            # it's not allowed to specify non-existent categories
            raise exc.HTTPBadRequest(msg)

        categories.append(ctg_obj)
    return categories


def _get_tags(tag_names, session=None):
    """
    Return existing tags object or create new ones
    :param tag_names: name of tags to associate with package, list
    :returns: list of Tag objects to associate with package, list
    """
    if session is None:
        session = db_session.get_session()
    tags = []
    for tag_name in tag_names:
        tag_obj = session.query(models.Tag).filter_by(name=tag_name).first()
        if tag_obj:
            tags.append(tag_obj)
        else:
            tag_record = models.Tag(name=tag_name)
            tags.append(tag_record)
    return tags


def _get_class_definitions(class_names, session=None):
    classes = []
    for name in class_names:
        class_record = models.Class(name=name)
        classes.append(class_record)
    return classes


def _do_replace(package, change):
    path = change['path'][0]
    value = change['value']
    calculate = {'categories': _get_categories,
                 'tags': _get_tags}
    if path in ('categories', 'tags'):
        existing_items = getattr(package, path)

        duplicates = list(set(i.name for i in existing_items) & set(value))
        unique_values = [x for x in value if x not in duplicates]
        items_to_replace = calculate[path](unique_values)

        # NOTE(efedorova): Replacing duplicate entities is not allowed,
        # so need to remove anything, but duplicates
        # and append everything but duplicates
        for item in list(existing_items):
            if item.name not in duplicates:
                existing_items.remove(item)

        existing_items.extend(items_to_replace)
    else:
        setattr(package, path, value)

    return package


def _do_add(package, change):
    # Only categories and tags support addition
    path = change['path'][0]
    value = change['value']

    calculate = {'categories': _get_categories,
                 'tags': _get_tags}
    items_to_add = calculate[path](value)
    for item in items_to_add:
        try:
            getattr(package, path).append(item)
        except AssertionError:
            msg = _('One of the specified {0} is already '
                    'associated with a package. Doing nothing.')
            LOG.warning(msg.format(path))
    return package


def _do_remove(package, change):
    # Only categories and tags support removal
    def find(seq, predicate):
        for elt in seq:
            if predicate(elt):
                return elt

    path = change['path'][0]
    values = change['value']

    current_values = getattr(package, path)
    for value in values:
        if value not in [i.name for i in current_values]:
            msg = _("Value '{0}' of property '{1}' "
                    "does not exist.").format(value, path)
            LOG.error(msg)
            raise exc.HTTPNotFound(msg)
        if path == 'categories' and len(current_values) == 1:
            msg = _("At least one category should be assigned to the package")
            LOG.error(msg)
            raise exc.HTTPBadRequest(msg)
        item_to_remove = find(current_values, lambda i: i.name == value)
        current_values.remove(item_to_remove)
    return package


def package_update(pkg_id, changes, context):
    """
    Update package information
    :param changes: parameters to update
    :returns: detailed information about new package, dict
    """

    operation_methods = {'add': _do_add,
                         'replace': _do_replace,
                         'remove': _do_remove}
    session = db_session.get_session()
    with session.begin():
        pkg = _package_get(pkg_id, session)
        _authorize_package(pkg, context)

        for change in changes:
            pkg = operation_methods[change['op']](pkg, change)
        session.add(pkg)
    return pkg


def package_search(filters, context):
    """
    Search packages with different filters
      * Admin is allowed to browse all the packages
      * Regular user is allowed to browse all packages belongs to user tenant
        and all other packages marked is_public.
        Also all packages should be enabled.
      * Use marker and limit for pagination:
        The typical pattern of limit and marker is to make an initial limited
        request and then to use the ID of the last package from the response
        as the marker parameter in a subsequent limited request.
    """

    def _validate_limit(value):
        if value is None:
            return
        try:
            value = int(value)
        except ValueError:
            msg = _("limit param must be an integer")
            LOG.error(msg)
            raise exc.HTTPBadRequest(explanation=msg)

        if value < 0:
            msg = _("limit param must be positive")
            LOG.error(msg)
            raise exc.HTTPBadRequest(explanation=msg)

        return value

    def get_pkg_attr(package_obj, search_attr_name):
        return getattr(package_obj, SEARCH_MAPPING[search_attr_name])

    limit = _validate_limit(filters.get('limit'))

    session = db_session.get_session()
    pkg = models.Package

    # If the packages search specifies the inclusion of disabled packages,
    # we handle this differently for admins vs non-admins:
    # For admins: *don't* require pkg.enabled == True (no changes to query)
    # For non-admins: add an OR-condition to filter for packages that are owned
    #                 by the tenant in the current context
    # Otherwise: in all other cases, we return only enabled packages
    if filters.get('include_disabled', '').lower() == 'true':
        include_disabled = True
    else:
        include_disabled = False

    if context.is_admin:
        if not include_disabled:
            query = session.query(pkg).filter(pkg.enabled)
        else:
            query = session.query(pkg)
    elif filters.get('owned', '').lower() == 'true':
        if not include_disabled:
            query = session.query(pkg).filter(
                pkg.owner_id == context.tenant & pkg.enabled
            )
        else:
            query = session.query(pkg).filter(pkg.owner_id == context.tenant)
    else:
        if not include_disabled:
            query = session.query(pkg).filter(
                or_((pkg.is_public & pkg.enabled),
                    (pkg.owner_id == context.tenant and pkg.enabled))
            )
        else:
            query = session.query(pkg).filter(
                or_((pkg.is_public & pkg.enabled),
                    pkg.owner_id == context.tenant)
            )

    if 'type' in filters.keys():
        query = query.filter(pkg.type == filters['type'].title())

    if 'category' in filters.keys():
        query = query.filter(pkg.categories.any(
            models.Category.name.in_(filters['category'])))
    if 'tag' in filters.keys():
        query = query.filter(pkg.tags.any(
            models.Tag.name.in_(filters['tag'])))
    if 'class_name' in filters.keys():
        query = query.filter(pkg.class_definitions.any(
            models.Class.name == filters['class_name']))
    if 'fqn' in filters.keys():
        query = query.filter(pkg.fully_qualified_name == filters['fqn'])

    if 'search' in filters.keys():
        fk_fields = {'categories': 'Category',
                     'tags': 'Tag',
                     'class_definitions': 'Class'}
        conditions = []

        for attr in dir(pkg):
            if attr.startswith('_'):
                continue
            if isinstance(getattr(pkg, attr),
                          attributes.InstrumentedAttribute):
                search_str = filters['search']
                for delim in ',;':
                    search_str = search_str.replace(delim, ' ')
                for key_word in search_str.split():
                    _word = '%{value}%'.format(value=key_word)
                    if attr in fk_fields.keys():
                        condition = getattr(pkg, attr).any(
                            getattr(models, fk_fields[attr]).name.like(_word))
                        conditions.append(condition)
                    else:
                        conditions.append(getattr(pkg, attr).like(_word))
        query = query.filter(or_(*conditions))

    sort_keys = filters.get('order_by', []) or ['created']
    for key in sort_keys:
        query = query.order_by(get_pkg_attr(pkg, key))

    marker = filters.get('marker')
    if marker is not None:
        # Note(efedorova): Copied from Glance
        #   Pagination works by requiring a unique sort_key, specified by sort_
        #   keys. (If sort_keys is not unique, then we risk looping through
        #   values.) We use the last row in the previous page as the 'marker'
        #   for pagination. So we must return values that follow the passed
        #   marker in the order. With a single-valued sort_key, this would
        #   be easy: sort_key > X. With a compound-values sort_key,
        #   (k1, k2, k3) we must do this to repeat the lexicographical
        #   ordering: (k1 > X1) or (k1 == X1 && k2 > X2) or
        #   (k1 == X1 && k2 == X2 && k3 > X3)

        model_marker = _package_get(marker, session)
        marker_values = []
        for sort_key in sort_keys:
            v = getattr(model_marker, sort_key)
            marker_values.append(v)

        # Build up an array of sort criteria as in the docstring
        criteria_list = []
        for i in range(len(sort_keys)):
            crit_attrs = []
            for j in range(i):
                model_attr = get_pkg_attr(pkg, sort_keys[j])
                crit_attrs.append((model_attr == marker_values[j]))

            model_attr = get_pkg_attr(pkg, sort_keys[i])
            crit_attrs.append((model_attr > marker_values[i]))

            criteria = sql.and_(*crit_attrs)
            criteria_list.append(criteria)
            f = sql.or_(*criteria_list)
            query = query.filter(f)

    if limit is not None:
        query = query.limit(limit)

    return query.all()


def package_upload(values, tenant_id):
    """
    Upload a package with new application
    :param values: parameters describing the new package
    :returns: detailed information about new package, dict
    """
    session = db_session.get_session()
    package = models.Package()

    composite_attr_to_func = {'categories': _get_categories,
                              'tags': _get_tags,
                              'class_definitions': _get_class_definitions}
    with session.begin():
        for attr, func in composite_attr_to_func.iteritems():
            if values.get(attr):
                result = func(values[attr], session)
                setattr(package, attr, result)
                del values[attr]

        package.update(values)
        package.owner_id = tenant_id
        package.save(session)
    return package


def package_delete(package_id):
    """
    Delete package information from the system ID of a package, string
    parameters to update
    """
    session = db_session.get_session()
    with session.begin():
        package = session.query(models.Package).get(package_id)

        session.delete(package)


def categories_list():
    session = db_session.get_session()
    return session.query(models.Category).all()


def category_get_names():
    session = db_session.get_session()
    categories = []
    for row in session.query(models.Category.name).all():
        for name in row:
            categories.append(name)
    return categories


def category_add(category_name):
    session = db_session.get_session()
    category = models.Category()

    with session.begin():
        category.update({'name': category_name})
        category.save(session)

    return category
