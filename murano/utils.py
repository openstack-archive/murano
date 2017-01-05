#    Copyright (c) 2013 Mirantis, Inc.
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

import contextlib
import functools
import os

from oslo_concurrency import lockutils
from oslo_log import log as logging
from oslo_utils import fileutils
from webob import exc

from murano.common.i18n import _
from murano.db import models
from murano.db.services import sessions
from murano.db import session as db_session
from murano.services import states

LOG = logging.getLogger(__name__)


def check_env(request, environment_id):
    unit = db_session.get_session()
    environment = unit.query(models.Environment).get(environment_id)
    if environment is None:
        msg = _('Environment with id {env_id}'
                ' not found').format(env_id=environment_id)
        LOG.error(msg)
        raise exc.HTTPNotFound(explanation=msg)

    if hasattr(request, 'context'):
        if (environment.tenant_id != request.context.tenant and not
                request.context.is_admin):
            msg = _('User is not authorized to access'
                    ' these tenant resources')
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)
    return environment


def check_session(request, environment_id, session, session_id):
    """Validate, that a session is ok."""
    if session is None:
        msg = _('Session <SessionId {id}> is not found').format(id=session_id)
        LOG.error(msg)
        raise exc.HTTPNotFound(explanation=msg)

    if session.environment_id != environment_id:
        msg = _('Session <SessionId {session_id}> is not tied '
                'with Environment <EnvId {environment_id}>').format(
                    session_id=session_id,
                    environment_id=environment_id)
        LOG.error(msg)
        raise exc.HTTPBadRequest(explanation=msg)

    check_env(request, environment_id)


def verify_env(func):
    @functools.wraps(func)
    def __inner(self, request, environment_id, *args, **kwargs):
        check_env(request, environment_id)
        return func(self, request, environment_id, *args, **kwargs)
    return __inner


def verify_env_template(func):
    @functools.wraps(func)
    def __inner(self, request, env_template_id, *args, **kwargs):
        unit = db_session.get_session()
        template = unit.query(models.EnvironmentTemplate).get(env_template_id)
        if template is None:
            msg = _('Environment Template with id {id} not found'
                    ).format(id=env_template_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)

        if hasattr(request, 'context'):
            if template.tenant_id != request.context.tenant:
                msg = _('User is not authorized to access'
                        ' this tenant resources')
                LOG.error(msg)
                raise exc.HTTPForbidden(explanation=msg)

        return func(self, request, env_template_id, *args, **kwargs)
    return __inner


def verify_session(func):
    @functools.wraps(func)
    def __inner(self, request, *args, **kwargs):
        if hasattr(request, 'context') and not request.context.session:
            msg = _('X-Configuration-Session header which indicates'
                    ' to the session is missed')
            LOG.error(msg)
            raise exc.HTTPBadRequest(explanation=msg)

        session_id = request.context.session

        unit = db_session.get_session()
        session = unit.query(models.Session).get(session_id)

        if session is None:
            msg = _('Session <SessionId {0}> is not found').format(session_id)
            LOG.error(msg)
            raise exc.HTTPNotFound(explanation=msg)

        if not sessions.SessionServices.validate(session):
            msg = _('Session <SessionId {0}> '
                    'is invalid: environment has been updated or '
                    'updating right now with other session').format(session_id)
            LOG.error(msg)
            raise exc.HTTPForbidden(explanation=msg)

        if session.state == states.SessionState.DEPLOYING:
            msg = _('Session <SessionId {0}> is already in deployment state'
                    ).format(session_id)
            raise exc.HTTPForbidden(explanation=msg)
        return func(self, request, *args, **kwargs)
    return __inner


ExclusiveInterProcessLock = lockutils.InterProcessLock
if os.name == 'nt':
    # no shared locks on windows
    SharedInterProcessLock = lockutils.InterProcessLock
else:
    import fcntl

    class SharedInterProcessLock(lockutils.InterProcessLock):
        def trylock(self):
            # LOCK_EX instead of LOCK_EX
            fcntl.lockf(self.lockfile, fcntl.LOCK_SH | fcntl.LOCK_NB)

        def _do_open(self):
            # the file has to be open in read mode, therefore this method has
            # to be overridden
            basedir = os.path.dirname(self.path)
            if basedir:
                made_basedir = fileutils.ensure_tree(basedir)
                if made_basedir:
                    self.logger.debug(
                        'Created lock base path `%s`', basedir)
            # The code here is mostly copy-pasted from oslo_concurrency and
            # fasteners. The file has to be open with read permissions to be
            # suitable for shared locking
            if self.lockfile is None or self.lockfile.closed:
                try:
                    # ensure the file is there, but do not obtain an extra file
                    # descriptor, as closing it would release fcntl lock
                    fd = os.open(self.path, os.O_CREAT | os.O_EXCL)
                    os.close(fd)
                except OSError:
                    pass
                self.lockfile = open(self.path, 'r')


class ReaderWriterLock(lockutils.ReaderWriterLock):

    @contextlib.contextmanager
    def write_lock(self, blocking=True):
        """Context manager that grants a write lock.

        Will wait until no active readers. Blocks readers after acquiring.
        Raises a ``RuntimeError`` if an active reader attempts to acquire
        a lock.
        """
        timeout = None if blocking else 0.00001
        me = self._current_thread()
        i_am_writer = self.is_writer(check_pending=False)
        if self.is_reader() and not i_am_writer:
            raise RuntimeError("Reader %s to writer privilege"
                               " escalation not allowed" % me)
        if i_am_writer:
            # Already the writer; this allows for basic reentrancy.
            yield self
        else:
            with self._cond:
                self._pending_writers.append(me)
                while True:
                    # No readers, and no active writer, am I next??
                    if len(self._readers) == 0 and self._writer is None:
                        if self._pending_writers[0] == me:
                            self._writer = self._pending_writers.popleft()
                            break

                    # NOTE(kzaitsev): this actually means, that we can wait
                    # more than timeout times, since if we get True value we
                    # would get another spin inside of the while loop
                    # Should we do anything about it?
                    acquired = self._cond.wait(timeout)
                    if not acquired:
                        yield False
                        return
            try:
                yield True
            finally:
                with self._cond:
                    self._writer = None
                    self._cond.notify_all()
