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

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

_ENFORCER = None


def reset():
    global _ENFORCER
    if _ENFORCER:
        _ENFORCER.clear()
    _ENFORCER = None


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


def init(default_rule=None, use_conf=True):
    global _ENFORCER
    if not _ENFORCER:
        LOG.debug("Enforcer is not present, recreating.")
        _ENFORCER = policy.Enforcer(CONF, use_conf=use_conf)
    _ENFORCER.load_rules()


def check(rule, ctxt, target=None, do_raise=True,
          exc=exceptions.HTTPForbidden):
    if target is None:
        target = {}
    creds = ctxt.to_dict()

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
    return check('context_is_admin', context,
                 context.to_dict(), do_raise=False)
