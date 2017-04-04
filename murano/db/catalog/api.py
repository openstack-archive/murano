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

from oslo_db import api as oslo_db_api
from oslo_db import exception as db_exceptions
from oslo_db.sqlalchemy import utils
from oslo_log import log as logging
import re
import sqlalchemy as sa
from sqlalchemy import or_
from sqlalchemy.orm import attributes
# TODO(ruhe) use exception declared in openstack/common/db
from webob import exc

from murano.common.i18n import _
from murano.db import models
from murano.db import session as db_session


SEARCH_MAPPING = {'fqn': 'fully_qualified_name',
                  'name': 'name',
                  'created': 'created'
                  }

LOG = logging.getLogger(__name__)


def _package_get(package_id, session):
    # TODO(sjmc7): update openstack/common and pull in
    # uuidutils, check that package_id_or_name resembles a
    # UUID before trying to treat it as one
    package = session.query(models.Package).get(package_id)
    if not package:
        msg = _("Package id '{pkg_id}' not found").format(pkg_id=package_id)
        LOG.error(msg)
        raise exc.HTTPNotFound(explanation=msg)

    return package


def _authorize_package(package, context, allow_public=False):

    if package.owner_id != context.tenant:
        if not allow_public:
            msg = _("Package '{pkg_id}' is not owned by tenant "
                    "'{tenant}'").format(pkg_id=package.id,
                                         tenant=context.tenant)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)
        if not package.is_public:
            msg = _("Package '{pkg_id}' is not public and not owned by "
                    "tenant '{tenant}' ").format(pkg_id=package.id,
                                                 tenant=context.tenant)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)


def package_get(package_id, context):
    """Return package details

       :param package_id: ID or name of a package, string
       :returns: detailed information about package, dict
    """
    session = db_session.get_session()
    package = _package_get(package_id, session)
    if not context.is_admin:
        _authorize_package(package, context, allow_public=True)
    return package


def _get_categories(category_names, session=None):
    """Return existing category objects or raise an exception.

       :param category_names: name of categories
                              to associate with package, list
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
            raise exc.HTTPBadRequest(explanation=msg)

        categories.append(ctg_obj)
    return categories


def _existing_tag(tag_name, session=None):
    if session is None:
        session = db_session.get_session()
    return session.query(models.Tag).filter_by(name=tag_name).first()


def _get_tags(tag_names, session=None):
    """Return existing tags object or create new ones

       :param tag_names: name of tags to associate with package, list
       :returns: list of Tag objects to associate with package, list
    """
    if session is None:
        session = db_session.get_session()
    tags = []
    # This function can be called inside a transaction and outside it.
    # In the former case this line is no-op, in the latter
    # starts a transaction we need to be inside a transaction, to correctly
    # handle DBDuplicateEntry errors without failing the whole transaction.
    # For more take a look at SQLAlchemy docs.
    with session.begin(subtransactions=True):
        for tag_name in tag_names:
            tag_obj = _existing_tag(tag_name, session)
            if not tag_obj:
                try:
                    # Start a new SAVEPOINT transaction. If it fails
                    # only the savepoint will be roll backed, not the
                    # whole transaction.
                    with session.begin(nested=True):
                        tag_obj = models.Tag(name=tag_name)
                        session.add(tag_obj)
                        session.flush(objects=[tag_obj])
                except db_exceptions.DBDuplicateEntry:
                    # new session is needed here to get access to the tag
                    tag_obj = _existing_tag(tag_name)
            tags.append(tag_obj)

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
            LOG.warning('One of the specified {path} is already associated'
                        ' with a package. Doing nothing.'.format(path=path))
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
            msg = _("Value '{value}' of property '{path}' "
                    "does not exist.").format(value=value, path=path)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)
        item_to_remove = find(current_values, lambda i: i.name == value)
        current_values.remove(item_to_remove)
    return package


def _get_packages_for_category(session, category_id):
    """Return detailed list of packages, belonging to the provided category

    :param session:
    :param category_id:
    :return: list of dictionaries, containing id, name and package fqn
    """
    pkg = models.Package
    packages = (session.query(pkg.id, pkg.name, pkg.fully_qualified_name)
                .filter(pkg.categories
                        .any(models.Category.id == category_id))
                .all())

    result_packages = []
    for package in packages:
        id, name, fqn = package
        result_packages.append({'id': id,
                                'name': name,
                                'fully_qualified_name': fqn})
    return result_packages


@oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
def package_update(pkg_id_or_name, changes, context):
    """Update package information

       :param changes: parameters to update
       :returns: detailed information about new package, dict
    """

    operation_methods = {'add': _do_add,
                         'replace': _do_replace,
                         'remove': _do_remove}
    session = db_session.get_session()
    with session.begin():
        pkg = _package_get(pkg_id_or_name, session)
        was_private = not pkg.is_public
        if not context.is_admin:
            _authorize_package(pkg, context)

        for change in changes:
            pkg = operation_methods[change['op']](pkg, change)
        became_public = pkg.is_public
        class_names = [clazz.name for clazz in pkg.class_definitions]
        if was_private and became_public:
            with db_session.get_lock("public_packages", session):
                _check_for_public_packages_with_fqn(session,
                                                    pkg.fully_qualified_name,
                                                    pkg.id)
                _check_for_existing_classes(session, class_names, None,
                                            check_public=True,
                                            ignore_package_with_id=pkg.id)

        session.add(pkg)
    return pkg


def package_search(filters, context, manage_public=False,
                   limit=None, catalog=False):
    """Search packages with different filters

      Catalog param controls the base query creation. Catalog queries
      only search packages a user can deploy. Non-catalog queries searches
      packages a user can edit.
      * Admin is allowed to browse all the packages
      * Regular user is allowed to browse all packages belongs to user tenant
        and all other packages marked is_public in catalog mode.
        In edit-mode non-admins are able to get own packages and public
        packages if corresponding policy is passed.
      * Use marker (inside filters param) and limit for pagination:
        The typical pattern of limit and marker is to make an initial limited
        request and then to use the ID of the last package from the response
        as the marker parameter in a subsequent limited request.
    """
    # pylint: disable=too-many-branches

    session = db_session.get_session()
    pkg = models.Package

    query = session.query(pkg)

    if catalog:
        # Only show packages one can deploy, i.e. own + public
        query = query.filter(or_(pkg.owner_id == context.tenant,
                                 pkg.is_public))
    else:
        # Show packages one can edit.
        if not context.is_admin:
            if manage_public:
                query = query.filter(or_(pkg.owner_id == context.tenant,
                                         pkg.is_public))
            else:
                query = query.filter(pkg.owner_id == context.tenant)
        # No else here admin can edit everything.

    if not filters.get('include_disabled', '').lower() == 'true':
        query = query.filter(pkg.enabled)

    if filters.get('owned', '').lower() == 'true':
        query = query.filter(pkg.owner_id == context.tenant)

    if 'type' in filters.keys():
        query = query.filter(pkg.type == filters['type'].title())

    if 'id' in filters:
        query = query.filter(models.Package.id.in_(filters['id']))
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
    if 'name' in filters.keys():
        query = query.filter(pkg.name == filters['name'])

    if 'search' in filters.keys():
        fk_fields = {'categories': 'Category',
                     'tags': 'Tag',
                     'class_definitions': 'Class'}
        # the default search order
        fields = ['name',
                  'fully_qualified_name',
                  'description',
                  'categories',
                  'tags',
                  'class_definitions',
                  'author']
        # split to searching words
        key_words = re.split(';|,', filters['search'])

        conditions = []
        order_cases = []
        sorted_fields = fields + list(set(dir(pkg)).difference(set(fields)))
        for index in range(0, len(sorted_fields)):
            attr = sorted_fields[index]
            if attr.startswith('_'):
                continue
            if not isinstance(getattr(pkg, attr),
                              attributes.InstrumentedAttribute):
                continue
            priority = min(index, len(fields))
            for key_word in key_words:
                _word = u'%{value}%'.format(value=key_word)
                if attr in fk_fields.keys():
                    condition = getattr(pkg, attr).any(
                        getattr(models, fk_fields[attr]).name.like(_word))
                    conditions.append(condition)
                    order_cases.append((condition, priority))
                elif isinstance(getattr(pkg, attr)
                                .property.columns[0].type, sa.String):
                    condition = getattr(pkg, attr).like(_word)
                    conditions.append(condition)
                    order_cases.append((condition, priority))

        order_expression = sa.case(order_cases).label("tmp_weight_uuid")
        query = query.filter(or_(*conditions)).order_by(order_expression.asc())

    sort_keys = [SEARCH_MAPPING[sort_key] for sort_key in
                 filters.get('order_by', ['name'])]
    sort_keys.append('id')
    marker = filters.get('marker')
    sort_dir = filters.get('sort_dir')

    if marker is not None:  # set marker to real object instead of its id
        marker = _package_get(marker, session)

    query = utils.paginate_query(
        query, pkg, limit, sort_keys, marker, sort_dir)

    return query.all()


@oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
def package_upload(values, tenant_id):
    """Upload a package with new application

       :param values: parameters describing the new package
       :returns: detailed information about new package, dict
    """
    session = db_session.get_session()
    package = models.Package()

    composite_attr_to_func = {'categories': _get_categories,
                              'tags': _get_tags,
                              'class_definitions': _get_class_definitions}
    is_public = values.get('is_public', False)

    if is_public:
        public_lock = db_session.get_lock("public_packages", session)
    else:
        public_lock = None
    tenant_lock = db_session.get_lock("classes_of_" + tenant_id, session)
    try:
        _check_for_existing_classes(session, values.get('class_definitions'),
                                    tenant_id, check_public=is_public)
        if is_public:
            _check_for_public_packages_with_fqn(
                session,
                values.get('fully_qualified_name'))
        for attr, func in composite_attr_to_func.items():
            if values.get(attr):
                result = func(values[attr], session)
                setattr(package, attr, result)
                del values[attr]
        package.update(values)
        package.owner_id = tenant_id
        package.save(session)
        tenant_lock.commit()
        if public_lock is not None:
            public_lock.commit()
    except Exception:
        tenant_lock.rollback()
        if public_lock is not None:
            public_lock.rollback()
        raise

    return package


@oslo_db_api.wrap_db_retry(max_retries=5, retry_on_deadlock=True)
def package_delete(package_id, context):
    """Delete a package by ID."""
    session = db_session.get_session()

    with session.begin():
        package = _package_get(package_id, session)
        if not context.is_admin and package.owner_id != context.tenant:
            raise exc.HTTPForbidden(
                explanation="Package is not owned by the"
                            " tenant '{0}'".format(context.tenant))
        session.delete(package)


def category_get(category_id, session=None, packages=False):
    """Return category details

       :param category_id: ID of a category, string
       :returns: detailed information about category, dict
    """
    if not session:
        session = db_session.get_session()

    category = session.query(models.Category).get(category_id)
    if not category:
        msg = _("Category id '{id}' not found").format(id=category_id)
        LOG.error(msg)
        raise exc.HTTPNotFound(msg)
    if packages:
        category.packages = _get_packages_for_category(session, category_id)
    return category


def categories_list(filters=None, limit=None, marker=None):
    if filters is None:
        filters = {}
    sort_keys = filters.get('sort_keys', ['name'])
    sort_dir = filters.get('sort_dir', 'asc')

    session = db_session.get_session()
    query = session.query(models.Category)
    if marker is not None:
        marker = category_get(marker, session)

    query = utils.paginate_query(
        query, models.Category, limit, sort_keys, marker, sort_dir)
    return query.all()


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
        # NOTE(kzaitsev) update package_count, so we can safely access from
        # outside the session
        category.package_count = 0
        category.save(session)

    return category


def category_delete(category_id):
    """Delete a category by ID."""
    session = db_session.get_session()

    with session.begin():
        category = session.query(models.Category).get(category_id)
        if not category:
            msg = _("Category id '{id}' not found").format(id=category_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(msg)
        session.delete(category)


def _check_for_existing_classes(session, class_names, tenant_id,
                                check_public=False,
                                ignore_package_with_id=None):
    if not class_names:
        return
    q = session.query(models.Class.name).filter(
        models.Class.name.in_(class_names))
    private_filter = None
    public_filter = None
    predicate = None
    if tenant_id is not None:
        private_filter = models.Class.package.has(
            models.Package.owner_id == tenant_id)
    if check_public:
        public_filter = models.Class.package.has(
            models.Package.is_public)
    if private_filter is not None and public_filter is not None:
        predicate = sa.or_(private_filter, public_filter)
    elif private_filter is not None:
        predicate = private_filter
    elif public_filter is not None:
        predicate = public_filter
    if predicate is not None:
        q = q.filter(predicate)
    if ignore_package_with_id is not None:
        q = q.filter(models.Class.package_id != ignore_package_with_id)
    if q.first() is not None:
        msg = _('Class with the same full name is already '
                'registered in the visibility scope')
        LOG.error(msg)
        raise exc.HTTPConflict(msg)


def _check_for_public_packages_with_fqn(session, fqn,
                                        ignore_package_with_id=None):
    q = session.query(models.Package.id).\
        filter(models.Package.is_public).\
        filter(models.Package.fully_qualified_name == fqn)
    if ignore_package_with_id is not None:
        q = q.filter(models.Package.id != ignore_package_with_id)
    if q.first() is not None:
        msg = _('Package with the same Name is already made public')
        LOG.error(msg)
        raise exc.HTTPConflict(msg)
