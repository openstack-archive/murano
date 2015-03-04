# Copyright (c) 2015 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import contextlib
import logging
import os
import time
import zipfile

from heatclient import client as heatclient
from keystoneclient import exceptions as ks_exceptions
from keystoneclient.v2_0 import client as ksclient
from muranoclient import client as mclient
import muranoclient.common.exceptions as exceptions

from murano.services import states
import murano.tests.functional.engine.config as cfg

CONF = cfg.cfg.CONF

LOG = logging.getLogger(__name__)


@contextlib.contextmanager
def ignored(*exceptions):
    try:
        yield
    except exceptions:
        pass


def memoize(f):
    """Decorator, which saves result of a decorated function
    to cache.
    TTL for cache is 1800 sec

    :param f: decorated function
    :return: saved result of a decorated function
    """
    cache = {}

    def decorated_function(*args):
        if args in cache:
            if time.time() - cache[args][1] < 1800:
                return cache[args][0]
            else:
                cache[args] = (f(*args), time.time())
                return cache[args][0]
        else:
            cache[args] = (f(*args), time.time())
            return cache[args][0]

    return decorated_function


class ZipUtilsMixin(object):
    @staticmethod
    def zip_dir(parent_dir, dir):
        abs_path = os.path.join(parent_dir, dir)
        path_len = len(abs_path) + 1
        zip_file = abs_path + ".zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            for dir_name, _, files in os.walk(abs_path):
                for filename in files:
                    fn = os.path.join(dir_name, filename)
                    zf.write(fn, fn[path_len:])
        return zip_file


class DeployTestMixin(ZipUtilsMixin):
    cfg.load_config()

    @staticmethod
    @memoize
    def keystone_client():
        return ksclient.Client(username=CONF.murano.user,
                               password=CONF.murano.password,
                               tenant_name=CONF.murano.tenant,
                               auth_url=CONF.murano.auth_url)

    @classmethod
    @memoize
    def heat_client(cls):
        heat_url = cls.keystone_client().service_catalog.url_for(
            service_type='orchestration', endpoint_type='publicURL')
        return heatclient.Client('1',
                                 endpoint=heat_url,
                                 token=cls.keystone_client().auth_token)

    @classmethod
    def get_murano_url(cls):
        try:
            url = cls.keystone_client().service_catalog.url_for(
                service_type='application_catalog', endpoint_type='publicURL')
        except ks_exceptions.EndpointNotFound:
            url = CONF.murano.murano_url
            LOG.warning("Murano endpoint not found in Keystone. Using CONF.")
        return url if 'v1' not in url else "/".join(
            url.split('/')[:url.split('/').index('v1')])

    @classmethod
    @memoize
    def murano_client(cls):
        murano_url = cls.get_murano_url()
        return mclient.Client('1',
                              endpoint=murano_url,
                              token=cls.keystone_client().auth_token)

    @classmethod
    def init_list(cls, list_name):
        if not hasattr(cls, list_name):
            setattr(cls, list_name, [])

    @classmethod
    def upload_package(cls, package_name, body, app):
        files = {'%s' % package_name: open(app, 'rb')}
        package = cls.murano_client().packages.create(body, files)
        cls.init_list("_packages")
        cls._packages.append(package)
        return package

    @classmethod
    def environment_delete(cls, environment_id, timeout=180):
        cls.murano_client().environments.delete(environment_id)

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                cls.murano_client().environments.get(environment_id)
            except exceptions.HTTPNotFound:
                return
        err_msg = ('Environment {0} was not deleted in {1} seconds'.
                   format(environment_id, timeout))
        LOG.error(err_msg)
        raise RuntimeError(err_msg)

    @classmethod
    def deploy_apps(cls, name, *apps):
        environment = cls.murano_client().environments.create({'name': name})
        cls.init_list("_environments")
        cls._environments.append(environment)
        session = cls.murano_client().sessions.configure(environment.id)
        for app in apps:
            cls.murano_client().services.post(
                environment.id,
                path='/',
                data=app,
                session_id=session.id)
        cls.murano_client().sessions.deploy(environment.id, session.id)
        return environment

    @staticmethod
    def wait_for_final_status(environment, timeout=300):
        start_time = time.time()
        status = environment.manager.get(environment.id).status
        while states.SessionState.DEPLOYING == status:
            if time.time() - start_time > timeout:
                err_msg = ('Deployment not finished in {0} seconds'
                           .format(timeout))
                LOG.error(err_msg)
                raise RuntimeError(err_msg)
            time.sleep(5)
            status = environment.manager.get(environment.id).status
        dep = environment.manager.api.deployments.list(environment.id)
        reports = environment.manager.api.deployments.reports(environment.id,
                                                              dep[0].id)
        return status, ", ".join([r.text for r in reports])

    @classmethod
    def purge_environments(cls):
        cls.init_list("_environments")
        try:
            for env in cls._environments:
                with ignored(Exception):
                    cls.environment_delete(env.id)
        finally:
            cls._environments = []

    @classmethod
    def purge_uploaded_packages(cls):
        cls.init_list("_packages")
        try:
            for pkg in cls._packages:
                with ignored(Exception):
                    cls.murano_client().packages.delete(pkg.id)
        finally:
            cls._packages = []
        cls.init_list("_package_files")
        try:
            for pkg_file in cls._package_files:
                os.remove(pkg_file)
        finally:
            cls._package_files = []
