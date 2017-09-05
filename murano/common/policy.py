#    Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

# Based on designate/policy.py

from oslo_config import cfg
from oslo_log import log as logging
from oslo_policy import policy
from webob import exc as exceptions

from murano.common import policies

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

_ENFORCER = None


def reset():
    global _ENFORCER
    if _ENFORCER:
        _ENFORCER.clear()
    _ENFORCER = None


def init(use_conf=True):
    global _ENFORCER
    if not _ENFORCER:
        LOG.debug("Enforcer is not present, recreating.")
        _ENFORCER = policy.Enforcer(CONF, use_conf=use_conf)
        register_rules(_ENFORCER)


def set_rules(data, default_rule=None, overwrite=True):
    default_rule = default_rule or cfg.CONF.policy_default_rule
    if not _ENFORCER:
        LOG.debug("Enforcer not present, recreating at rules stage.")
        init()

    if default_rule:
        _ENFORCER.default_rule = default_rule

    LOG.debug("Loading rules {rules}, default: {def_rule}, overwrite: "
              "{overwrite}".format(rules=data, def_rule=default_rule,
                                   overwrite=overwrite))

    if isinstance(data, dict):
        rules = policy.Rules.from_dict(data, default_rule)
    else:
        rules = policy.Rules.load_json(data, default_rule)

    _ENFORCER.set_rules(rules, overwrite=overwrite)


def check(rule, ctxt, target=None, do_raise=True, exc=None):
    """Verify that the rule is valid on the target in this context.

    :param rule: String representing the action to be checked, which should
                 be colon-separated for clarity.
    :param ctxt: Request context from which user credentials are extracted.
    :param target: Dictionary representing the object of the action for object
                   creation; this should be a dictionary representing the
                   location of the object, e.g. {'environment_id':
                   object.environment_id}
    :param do_raise: Whether to raise an exception or not if the check fails.
    :param exc: Class of the exception to raise if the check fails.
    :raises exceptions.HTTPForbidden: If verification fails. Or if 'exc' is
                                      specified it will raise an exception of
                                      that type.
    """
    init()

    if target is None:
        target = {}
    creds = ctxt.to_dict()
    if not exc:
        exc = exceptions.HTTPForbidden

    try:
        result = _ENFORCER.enforce(rule, target, creds, do_raise, exc)
    except Exception:
        result = False
        raise
    else:
        return result
    finally:
        extra = {'policy': {'rule': rule, 'target': target}}

        if result:
            LOG.debug("Policy check succeeded for rule {rule} on target "
                      "{target}".format(rule=rule, target=repr(target),
                                        extra=extra))
        else:
            LOG.debug("Policy check failed for rule {rule} on target: "
                      "{target}".format(rule=rule, target=repr(target),
                                        extra=extra))


def check_is_admin(context):
    """Check if the given context is associated with an admin role.

       :param context: Murano request context
       :returns: A non-False value if context role is admin.
    """
    return check('context_is_admin', context, context.to_dict(),
                 do_raise=False)


def register_rules(enforcer):
    enforcer.register_defaults(policies.list_rules())
