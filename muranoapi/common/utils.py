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

import eventlet
from functools import wraps
from muranoapi.openstack.common import log as logging

log = logging.getLogger(__name__)


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2):
    """Retry calling the decorated function using an exponential backoff.

    http://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    original from: http://wiki.python.org/moin/PythonDecoratorLibrary#Retry

    :param ExceptionToCheck: the exception to check. may be a tuple of
        exceptions to check
    :type ExceptionToCheck: Exception or tuple
    :param tries: number of times to try (not retry) before giving up
    :type tries: int
    :param delay: initial delay between retries in seconds
    :type delay: int
    :param backoff: backoff multiplier e.g. value of 2 will double the delay
        each retry
    :type backoff: int
    """

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            forever = mtries == -1
            while forever or mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:

                    log.exception(e)
                    log.info("Retrying in {0} seconds...".format(mdelay))

                    eventlet.sleep(mdelay)

                    if not forever:
                        mtries -= 1

                    if mdelay < 60:
                        mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry

    return deco_retry


def handle(f):
    """Handles exception in wrapped function and writes to log."""

    @wraps(f)
    def f_handle(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            log.exception(e)

    return f_handle
