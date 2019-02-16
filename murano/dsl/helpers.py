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

import collections
import contextlib
import functools
import gc
import inspect
import itertools
import re
import sys
import uuid
import weakref


import eventlet.greenpool
import eventlet.greenthread
from oslo_config import cfg
import semantic_version
import six
from yaql.language import contexts
import yaql.language.exceptions
import yaql.language.expressions
from yaql.language import utils as yaqlutils


from murano.dsl import constants
from murano.dsl import dsl_types
from murano.dsl import exceptions

_threads_sequencer = 0
# type string: ns.something.MyApp[/1.2.3-alpha][@my.package.fqn]
TYPE_RE = re.compile(r'([a-zA-Z0-9_.]+)(?:/([^@]+))?(?:@([a-zA-Z0-9_.]+))?$')
CONF = cfg.CONF


def evaluate(value, context, freeze=True):
    list_type = tuple if freeze else list
    dict_type = yaqlutils.FrozenDict if freeze else dict
    set_type = frozenset if freeze else set

    if isinstance(value, (dsl_types.YaqlExpression,
                          yaql.language.expressions.Statement)):
        return value(context)
    elif isinstance(value, yaqlutils.MappingType):
        return dict_type(
            (evaluate(d_key, context, freeze),
             evaluate(d_value, context, freeze))
            for d_key, d_value in value.items())
    elif yaqlutils.is_sequence(value):
        return list_type(evaluate(t, context, freeze) for t in value)
    elif isinstance(value, yaqlutils.SetType):
        return set_type(evaluate(t, context, freeze) for t in value)
    elif yaqlutils.is_iterable(value):
        return list_type(
            evaluate(t, context, freeze)
            for t in yaqlutils.limit_iterable(
                value, CONF.murano.dsl_iterators_limit))
    elif isinstance(value, dsl_types.MuranoObjectInterface):
        return value.object
    else:
        return value


def merge_lists(list1, list2):
    result = []
    for item in list1 + list2:
        if item not in result:
            result.append(item)
    return result


def merge_dicts(dict1, dict2, max_levels=0):
    result = {}
    for key, value1 in dict1.items():
        result[key] = value1
        if key in dict2:
            value2 = dict2[key]
            if type(value2) != type(value1):
                if ((isinstance(value1,
                                six.string_types) or value1 is None) and
                        (isinstance(value2,
                                    six.string_types) or value2 is None)):
                    continue
                raise TypeError()
            if max_levels != 1 and isinstance(value2, dict):
                result[key] = merge_dicts(
                    value1, value2,
                    0 if max_levels == 0 else max_levels - 1)
            elif max_levels != 1 and isinstance(value2, list):
                result[key] = merge_lists(value1, value2)
            else:
                result[key] = value2
    for key, value1 in dict2.items():
        if key not in result:
            result[key] = value1
    return result


def generate_id():
    return uuid.uuid4().hex


def parallel_select(collection, func, limit=1000):
    # workaround for eventlet issue 232
    # https://github.com/eventlet/eventlet/issues/232
    context = get_context()
    object_store = get_object_store()

    def wrapper(element):
        try:
            with with_object_store(object_store), contextual(context):
                return func(element), False, None
        except Exception as e:
            return e, True, sys.exc_info()[2]

    gpool = eventlet.greenpool.GreenPool(limit)
    result = list(gpool.imap(wrapper, collection))
    try:
        exception = next(t for t in result if t[1])
    except StopIteration:
        return map(lambda t: t[0], result)
    else:
        six.reraise(type(exception[0]), exception[0], exception[2])


def enum(**enums):
    return type('Enum', (), enums)


def get_context():
    current_thread = eventlet.greenthread.getcurrent()
    return getattr(current_thread, constants.TL_CONTEXT, None)


def get_executor():
    store = get_object_store()
    return None if store is None else store.executor


def get_type(context=None):
    context = context or get_context()
    return context[constants.CTX_TYPE]


def get_execution_session():
    executor = get_executor()
    return None if executor is None else executor.execution_session


def get_object_store():
    current_thread = eventlet.greenthread.getcurrent()
    return getattr(current_thread, constants.TL_OBJECT_STORE, None)


def get_package_loader():
    executor = get_executor()
    return None if executor is None else executor.package_loader


def get_this(context=None):
    context = context or get_context()
    return context[constants.CTX_THIS]


def get_caller_context(context=None):
    context = context or get_context()
    return context[constants.CTX_CALLER_CONTEXT]


def get_attribute_store():
    executor = get_executor()
    return None if executor is None else executor.attribute_store


def get_current_instruction(context=None):
    context = context or get_context()
    return context[constants.CTX_CURRENT_INSTRUCTION]


def get_current_method(context=None):
    context = context or get_context()
    return context[constants.CTX_CURRENT_METHOD]


def get_yaql_engine(context=None):
    context = context or get_context()
    return None if context is None else context[constants.CTX_YAQL_ENGINE]


def get_current_exception(context=None):
    context = context or get_context()
    return context[constants.CTX_CURRENT_EXCEPTION]


def are_property_modifications_allowed(context=None):
    context = context or get_context()
    return context[constants.CTX_ALLOW_PROPERTY_WRITES] or False


def get_names_scope(context=None):
    context = context or get_context()
    return context[constants.CTX_NAMES_SCOPE]


def get_class(name, context=None):
    context = context or get_context()
    murano_type = get_names_scope(context)
    name = murano_type.namespace_resolver.resolve_name(name)
    return murano_type.package.find_class(name)


def get_contract_passkey():
    current_thread = eventlet.greenthread.getcurrent()
    return getattr(current_thread, constants.TL_CONTRACT_PASSKEY, None)


def is_objects_dry_run_mode():
    current_thread = eventlet.greenthread.getcurrent()
    return bool(getattr(current_thread, constants.TL_OBJECTS_DRY_RUN, False))


def get_current_thread_id():
    global _threads_sequencer

    current_thread = eventlet.greenthread.getcurrent()
    thread_id = getattr(current_thread, constants.TL_ID, None)
    if thread_id is None:
        thread_id = 'T' + str(_threads_sequencer)
        _threads_sequencer += 1
        setattr(current_thread, constants.TL_ID, thread_id)
    return thread_id


@contextlib.contextmanager
def thread_local_attribute(name, value):
    current_thread = eventlet.greenthread.getcurrent()
    old_value = getattr(current_thread, name, None)
    if value is not None:
        setattr(current_thread, name, value)
    elif hasattr(current_thread, name):
        delattr(current_thread, name)
    try:
        yield
    finally:
        if old_value is not None:
            setattr(current_thread, name, old_value)
        elif hasattr(current_thread, name):
            delattr(current_thread, name)


def contextual(ctx):
    return thread_local_attribute(constants.TL_CONTEXT, ctx)


def with_object_store(object_store):
    return thread_local_attribute(constants.TL_OBJECT_STORE, object_store)


def parse_version_spec(version_spec):
    if isinstance(version_spec, semantic_version.Spec):
        return normalize_version_spec(version_spec)
    if isinstance(version_spec, semantic_version.Version):
        return normalize_version_spec(
            semantic_version.Spec('==' + str(version_spec)))
    if not version_spec:
        version_spec = '0'
    version_spec = re.sub('\s+', '', str(version_spec))

    # NOTE(kzaitsev): semantic_version 2.3.X thinks that '=0' is not
    # a valid version spec and only accepts '==0', this regexp adds
    # an extra '=' before such specs
    version_spec = re.sub(r'^=(\d)', r'==\1', version_spec)

    if version_spec[0].isdigit():
        version_spec = '==' + str(version_spec)
    version_spec = semantic_version.Spec(version_spec)
    return normalize_version_spec(version_spec)


def parse_version(version):
    if isinstance(version, semantic_version.Version):
        return version
    if not version:
        version = '0'
    return semantic_version.Version.coerce(str(version))


def traverse(seed, producer=None, track_visited=True):
    if not yaqlutils.is_iterable(seed):
        seed = [seed]
    visited = None if not track_visited else set()
    queue = collections.deque(seed)
    while queue:
        item = queue.popleft()
        if track_visited:
            if item in visited:
                continue
            visited.add(item)
        produced = (yield item)
        if produced is None and producer:
            produced = producer(item)
        if produced:
            queue.extend(produced)


def cast(obj, murano_class, pov_or_version_spec=None):
    if isinstance(obj, dsl_types.MuranoObjectInterface):
        obj = obj.object
    if isinstance(pov_or_version_spec, dsl_types.MuranoType):
        pov_or_version_spec = pov_or_version_spec.package
    elif isinstance(pov_or_version_spec, six.string_types):
        pov_or_version_spec = parse_version_spec(pov_or_version_spec)

    if isinstance(murano_class, dsl_types.MuranoTypeReference):
        murano_class = murano_class.type
    if isinstance(murano_class, dsl_types.MuranoType):
        if pov_or_version_spec is None:
            pov_or_version_spec = parse_version_spec(murano_class.version)
        murano_class = murano_class.name

    candidates = []
    for cls in itertools.chain((obj.type,), obj.type.ancestors()):
        if cls.name != murano_class:
            continue
        elif isinstance(pov_or_version_spec, semantic_version.Version):
            if cls.version != pov_or_version_spec:
                continue
        elif isinstance(pov_or_version_spec, semantic_version.Spec):
            if cls.version not in pov_or_version_spec:
                continue
        elif isinstance(pov_or_version_spec, dsl_types.MuranoPackage):
            requirement = pov_or_version_spec.requirements.get(
                cls.package.name)
            if requirement is None:
                raise exceptions.NoClassFound(murano_class)
            if cls.version not in requirement:
                continue
        elif pov_or_version_spec is not None:
            raise ValueError('pov_or_version_spec of unsupported '
                             'type {0}'.format(type(pov_or_version_spec)))
        candidates.append(cls)
    if not candidates:
        raise exceptions.NoClassFound(murano_class)
    elif len(candidates) > 1:
        raise exceptions.AmbiguousClassName(murano_class)
    return obj.cast(candidates[0])


def is_instance_of(obj, class_name, pov_or_version_spec=None):
    if not isinstance(obj, (dsl_types.MuranoObject,
                            dsl_types.MuranoObjectInterface)):
        return False
    try:
        cast(obj, class_name, pov_or_version_spec)
        return True
    except (exceptions.NoClassFound, exceptions.AmbiguousClassName):
        return False


def memoize(func):
    cache = {}
    return get_memoize_func(func, cache)


def get_memoize_func(func, cache):
    @functools.wraps(func)
    def wrap(*args):
        if args not in cache:
            result = func(*args)
            cache[args] = result
            return result
        else:
            return cache[args]
    return wrap


def normalize_version_spec(version_spec):
    def coerce(v):
        return semantic_version.Version('{0}.{1}.{2}'.format(
            v.major, v.minor or 0, v.patch or 0
        ))

    def increment(v):
        # NOTE(ativelkov): replace these implementations with next_minor() and
        # next_major() calls when the semantic_version is updated in global
        # requirements.
        if v.minor is None:
            return semantic_version.Version(
                '.'.join(str(x) for x in [v.major + 1, 0, 0]))
        else:
            return semantic_version.Version(
                '.'.join(str(x) for x in [v.major, v.minor + 1, 0]))

    def extend(v):
        return semantic_version.Version(str(v) + '-0')

    transformations = {
        '>': [('>=', (increment, extend))],
        '>=': [('>=', (coerce,))],
        '<': [('<', (coerce, extend))],
        '<=': [('<', (increment, extend))],
        '!=': [('>=', (increment, extend))],
        '==': [('>=', (coerce,)), ('<', (increment, coerce, extend))]
    }

    new_parts = []
    for item in version_spec.specs:
        if item.kind == '*':
            continue
        elif item.spec.patch is not None:
            new_parts.append(str(item))
        else:
            for op, funcs in transformations[item.kind]:
                new_parts.append('{0}{1}'.format(
                    op,
                    six.moves.reduce(lambda v, f: f(v), funcs, item.spec)
                ))
    if not new_parts:
        return semantic_version.Spec('*')
    return semantic_version.Spec(*new_parts)


semver_to_api_map = {
    '>': 'gt',
    '>=': 'ge',
    '<': 'lt',
    '<=': 'le',
    '!=': 'ne',
    '==': 'eq'
}


def breakdown_spec_to_query(normalized_spec):
    res = []
    for item in normalized_spec.specs:
        if item.kind == '*':
            continue
        else:
            res.append("%s:%s" % (semver_to_api_map[item.kind],
                                  item.spec))
    return res


def link_contexts(parent_context, context):
    if not context:
        return parent_context
    return contexts.LinkedContext(parent_context, context)


def inspect_is_static(cls, name):
    m = cls.__dict__.get(name)
    if m is None:
        return False
    return isinstance(m, staticmethod)


def inspect_is_classmethod(cls, name):
    m = cls.__dict__.get(name)
    if m is None:
        return False
    return isinstance(m, classmethod)


def inspect_is_method(cls, name):
    m = getattr(cls, name, None)
    if m is None:
        return False
    return ((inspect.isfunction(m) or inspect.ismethod(m)) and not
            inspect_is_static(cls, name) and not
            inspect_is_classmethod(cls, name))


def inspect_is_property(cls, name):
    m = getattr(cls, name, None)
    if m is None:
        return False
    return inspect.isdatadescriptor(m)


def updated_dict(d, val):
    if d is None:
        d = {}
    else:
        d = d.copy()
    if val is not None:
        d.update(val)
    return d


def resolve_type(value, scope_type, return_reference=False):
    if value is None:
        return None
    if isinstance(scope_type, dsl_types.MuranoTypeReference):
        scope_type = scope_type.type
    if not isinstance(value, (dsl_types.MuranoType,
                              dsl_types.MuranoTypeReference)):
        name = scope_type.namespace_resolver.resolve_name(value)
        result = scope_type.package.find_class(name)
    else:
        result = value

    if isinstance(result, dsl_types.MuranoTypeReference):
        if return_reference:
            return result
        return result.type
    elif return_reference:
        return result.get_reference()
    return result


def parse_object_definition(spec, scope_type, context):
    if not isinstance(spec, yaqlutils.MappingType):
        return None

    if context:
        spec = evaluate(spec, context, freeze=False)
    else:
        spec = spec.copy()
    system_data = None
    type_obj = None
    props = {}
    ns_resolver = scope_type.namespace_resolver if scope_type else None
    for key in spec:
        if (ns_resolver and ns_resolver.is_typename(key, False) or
                isinstance(key, (dsl_types.MuranoTypeReference,
                                 dsl_types.MuranoType))):
            type_obj = resolve_type(key, scope_type)
            props = spec.pop(key) or {}
            system_data = spec
            break
    if system_data is None:
        props = spec
        if '?' in spec:
            system_data = spec.pop('?')
            obj_type = system_data.get('type')
            if isinstance(obj_type, dsl_types.MuranoTypeReference):
                type_obj = obj_type.type
            elif isinstance(obj_type, dsl_types.MuranoType):
                type_obj = obj_type
            elif obj_type:
                type_str, version_str, package_str = parse_type_string(
                    obj_type,
                    system_data.get('classVersion'),
                    system_data.get('package')
                )
                version_spec = parse_version_spec(version_str)
                package_loader = get_package_loader()
                if package_str:
                    package = package_loader.load_package(
                        package_str, version_spec)
                else:
                    package = package_loader.load_class_package(
                        type_str, version_spec)
                type_obj = package.find_class(type_str, False)
        else:
            system_data = {}

    return {
        'type': type_obj,
        'properties': yaqlutils.filter_parameters_dict(props),
        'id': system_data.get('id'),
        'name': system_data.get('name'),
        'metadata': system_data.get('metadata'),
        'destroyed': system_data.get('destroyed', False),
        'dependencies': system_data.get('dependencies', {}),
        'extra': {
            key: value for key, value in system_data.items()
            if key.startswith('_')
        }
    }


def assemble_object_definition(parsed, model_format=dsl_types.DumpTypes.Mixed):
    if model_format == dsl_types.DumpTypes.Inline:
        result = {
            parsed['type']: parsed['properties'],
            'id': parsed['id'],
            'name': parsed['name'],
            'metadata': parsed['metadata'],
            'dependencies': parsed['dependencies'],
            'destroyed': parsed['destroyed']
        }
        result.update(parsed['extra'])
        return result
    result = parsed['properties']
    header = {
        'id': parsed['id'],
        'name': parsed['name'],
        'metadata': parsed['metadata']
    }
    if parsed['destroyed']:
        header['destroyed'] = True
    header.update(parsed['extra'])
    result['?'] = header
    if model_format == dsl_types.DumpTypes.Mixed:
        header['type'] = parsed['type']
        return result
    elif model_format == dsl_types.DumpTypes.Serializable:
        cls = parsed['type']
        if cls:
            header['type'] = format_type_string(cls)
        return result
    else:
        raise ValueError('Invalid Serialization Type')


def function(c):
    if hasattr(c, 'im_func'):
        return c.im_func
    return c


def list_value(v):
    if v is None:
        return []
    if not yaqlutils.is_sequence(v):
        v = [v]
    return v


def weak_proxy(obj):
    if obj is None or isinstance(obj, weakref.ProxyType):
        return obj
    if isinstance(obj, weakref.ReferenceType):
        obj = obj()
    return weakref.proxy(obj)


def weak_ref(obj):
    class MuranoObjectWeakRef(weakref.ReferenceType):
        def __init__(self, murano_object):
            self.ref = weakref.ref(murano_object)
            self.object_id = murano_object.object_id

        def __call__(self):
            res = self.ref()
            if not res:
                object_store = get_object_store()
                if object_store:
                    res = object_store.get(self.object_id)
                    if res:
                        self.ref = weakref.ref(res)
            return res

    if obj is None or isinstance(obj, weakref.ReferenceType):
        return obj

    if isinstance(obj, dsl_types.MuranoObject):
        return MuranoObjectWeakRef(obj)
    return weakref.ref(obj)


def parse_type_string(type_str, default_version, default_package):
    res = TYPE_RE.match(type_str)
    if res is None:
        return None
    parsed_type = res.group(1)
    parsed_version = res.group(2)
    parsed_package = res.group(3)
    return (
        parsed_type,
        default_version if parsed_version is None else parsed_version,
        default_package if parsed_package is None else parsed_package
    )


def format_type_string(type_obj):
    if isinstance(type_obj, dsl_types.MuranoTypeReference):
        type_obj = type_obj.type
    if isinstance(type_obj, dsl_types.MuranoType):
        return '{0}/{1}@{2}'.format(
            type_obj.name, type_obj.version, type_obj.package.name)
    else:
        raise ValueError('Invalid argument')


def patch_dict(dct, path, value):
    parts = path.split('.')
    for i in range(len(parts) - 1):
        if not isinstance(dct, dict):
            dct = None
            break
        dct = dct.get(parts[i])
    if isinstance(dct, dict):
        if value is yaqlutils.NO_VALUE:
            dct.pop(parts[-1])
        else:
            dct[parts[-1]] = value


def format_scalar(value):
    if isinstance(value, six.string_types):
        return "'{0}'".format(value)
    return six.text_type(value)


def is_passkey(value):
    passkey = get_contract_passkey()
    return passkey is not None and value is passkey


def find_object_owner(obj, predicate):
    p = obj.owner
    while p:
        if predicate(p):
            return p
        p = p.owner
    return None


# This function is not intended to be used in the code but is very useful
# for debugging object reference leaks
def walk_gc(obj, towards, handler):
    visited = set()
    queue = collections.deque([(obj, [])])
    while queue:
        item, trace = queue.popleft()
        if id(item) in visited:
            continue
        if handler(item):
            if towards:
                yield trace + [item]
            else:
                yield [item] + trace

        visited.add(id(item))
        if towards:
            try:
                queue.extend(
                    [(t, trace + [item]) for t in gc.get_referrers(item)]
                )
            except StopIteration:
                return
        else:
            try:
                queue.extend(
                    [(t, [item] + trace) for t in gc.get_referents(item)]
                )
            except StopIteration:
                return
