# Copyright 2012 OpenStack LLC.
# All Rights Reserved.
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

import sys
import uuid

import os
from glazierclient.common import exceptions
import prettytable
from glazierclient.openstack.common import importutils


# Decorator for cli-args
def arg(*args, **kwargs):
    def _decorator(func):
        # Because of the sematics of decorator composition if we just append
        # to the options list positional options will appear to be backwards.
        func.__dict__.setdefault('arguments', []).insert(0, (args, kwargs))
        return func
    return _decorator


def pretty_choice_list(l):
    return ', '.join("'%s'" % i for i in l)


def print_list(objs, fields, field_labels, formatters={}, sortby=0):
    pt = prettytable.PrettyTable([f for f in field_labels], caching=False)
    pt.align = 'l'

    for o in objs:
        row = []
        for field in fields:
            if field in formatters:
                row.append(formatters[field](o))
            else:
                data = getattr(o, field, None) or ''
                row.append(data)
        pt.add_row(row)
    print pt.get_string(sortby=field_labels[sortby])


def print_dict(d, formatters={}):
    pt = prettytable.PrettyTable(['Property', 'Value'], caching=False)
    pt.align = 'l'

    for field in d.keys():
        if field in formatters:
            pt.add_row([field, formatters[field](d[field])])
        else:
            pt.add_row([field, d[field]])
    print pt.get_string(sortby='Property')


def find_resource(manager, name_or_id):
    """Helper for the _find_* methods."""
    # first try to get entity as integer id
    try:
        if isinstance(name_or_id, int) or name_or_id.isdigit():
            return manager.get(int(name_or_id))
    except exceptions.NotFound:
        pass

    # now try to get entity as uuid
    try:
        uuid.UUID(str(name_or_id))
        return manager.get(name_or_id)
    except (ValueError, exceptions.NotFound):
        pass

    # finally try to find entity by name
    try:
        return manager.find(name=name_or_id)
    except exceptions.NotFound:
        msg = "No %s with a name or ID of '%s' exists." % \
              (manager.resource_class.__name__.lower(), name_or_id)
        raise exceptions.CommandError(msg)


def string_to_bool(arg):
    return arg.strip().lower() in ('t', 'true', 'yes', '1')


def env(*vars, **kwargs):
    """Search for the first defined of possibly many env vars

    Returns the first environment variable defined in vars, or
    returns the default defined in kwargs.
    """
    for v in vars:
        value = os.environ.get(v, None)
        if value:
            return value
    return kwargs.get('default', '')


def import_versioned_module(version, submodule=None):
    module = 'glazierclient.v%s' % version
    if submodule:
        module = '.'.join((module, submodule))
    return importutils.import_module(module)


def exit(msg=''):
    if msg:
        print >> sys.stderr, msg
    sys.exit(1)
