# Copyright (c) 2016 AT&T Corp
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

from keystoneauth1 import loading as ka_loading

from murano.common import auth_utils
from murano.tests.unit import base

from oslo_config import cfg


class TestAuthUtils(base.MuranoTestCase):

    def setUp(self):
        super(TestAuthUtils, self).setUp()
        # Register the Password auth plugin options,
        # so we can use CONF.set_override
        password_option = ka_loading.get_auth_plugin_conf_options('password')
        cfg.CONF.register_opts(password_option,
                               group=auth_utils.CFG_MURANO_AUTH_GROUP)
        self.addCleanup(
            cfg.CONF.unregister_opts,
            password_option,
            group=auth_utils.CFG_MURANO_AUTH_GROUP)
        self.addCleanup(mock.patch.stopall)

    def _init_mock_cfg(self):
        mock_auth_obj = mock.patch.object(auth_utils, 'ka_loading',
                                          spec_set=ka_loading).start()
        mock_auth_obj.load_auth_from_conf_options.return_value = \
            mock.sentinel.auth
        mock_auth_obj.load_session_from_conf_options.\
            return_value = mock.sentinel.session
        cfg.CONF.set_override('auth_type',
                              'password',
                              auth_utils.CFG_MURANO_AUTH_GROUP)
        cfg.CONF.set_override('www_authenticate_uri',
                              'foo_www_authenticate_uri',
                              auth_utils.CFG_MURANO_AUTH_GROUP)
        cfg.CONF.set_override('auth_url',
                              'foo_auth_url',
                              auth_utils.CFG_MURANO_AUTH_GROUP)
        cfg.CONF.set_override('username',
                              'fakeuser',
                              auth_utils.CFG_MURANO_AUTH_GROUP)
        cfg.CONF.set_override('password',
                              'fakepass',
                              auth_utils.CFG_MURANO_AUTH_GROUP)
        cfg.CONF.set_override('user_domain_name',
                              'Default',
                              auth_utils.CFG_MURANO_AUTH_GROUP)
        cfg.CONF.set_override('project_domain_name',
                              'Default',
                              auth_utils.CFG_MURANO_AUTH_GROUP)
        cfg.CONF.set_override('project_name',
                              'fakeproj',
                              auth_utils.CFG_MURANO_AUTH_GROUP)
        return mock_auth_obj

    def test_get_keystone_auth(self):
        mock_identity = self._init_mock_cfg()

        expected_auth = mock.sentinel.auth
        actual_auth = auth_utils._get_keystone_auth()

        self.assertEqual(expected_auth, actual_auth)
        mock_identity.load_auth_from_conf_options.assert_called_once_with(
            cfg.CONF, auth_utils.CFG_MURANO_AUTH_GROUP)

    def test_get_keystone_with_trust_id(self):
        mock_ka_loading = self._init_mock_cfg()

        expected_kwargs = {
            'project_name': None,
            'project_domain_name': None,
            'project_id': None,
            'trust_id': mock.sentinel.trust_id
        }
        expected_auth = mock.sentinel.auth
        actual_auth = auth_utils._get_keystone_auth(mock.sentinel.trust_id)

        self.assertEqual(expected_auth, actual_auth)
        mock_ka_loading.load_auth_from_conf_options.assert_called_once_with(
            cfg.CONF,
            auth_utils.CFG_MURANO_AUTH_GROUP,
            **expected_kwargs)

    @mock.patch.object(auth_utils, 'ks_client', autospec=True)
    @mock.patch.object(auth_utils, '_get_session', autospec=True)
    def test_create_keystone_admin_client(self, mock_get_sess, mock_ks_client):
        self._init_mock_cfg()
        mock_get_sess.return_value = mock.sentinel.session
        mock_ks_client.Client.return_value = mock.sentinel.ks_admin_client

        result = auth_utils._create_keystone_admin_client()

        self.assertEqual(result, mock.sentinel.ks_admin_client)
        self.assertTrue(mock_get_sess.called)
        mock_ks_client.Client.assert_called_once_with(
            session=mock.sentinel.session)

    @mock.patch.object(auth_utils, '_get_session', autospec=True)
    @mock.patch.object(auth_utils, '_get_keystone_auth', autospec=True)
    @mock.patch.object(
        auth_utils.helpers, 'get_execution_session', autospec=True)
    def test_get_client_session(self, mock_get_execution_session,
                                mock_get_keystone_auth, mock_get_session):
        mock_exec_session = mock.Mock(trust_id=mock.sentinel.trust_id)
        mock_get_execution_session.return_value = mock_exec_session
        mock_get_keystone_auth.return_value = mock.sentinel.auth
        mock_get_session.return_value = mock.sentinel.session

        session = auth_utils.get_client_session(conf=mock.sentinel.conf)

        self.assertEqual(mock.sentinel.session, session)
        mock_get_execution_session.assert_called_once_with()
        mock_get_keystone_auth.assert_called_once_with(mock.sentinel.trust_id)
        mock_get_session.assert_called_once_with(
            auth=mock.sentinel.auth,
            conf_section=mock.sentinel.conf)

    @mock.patch.object(auth_utils, 'get_token_client_session', autospec=True)
    @mock.patch.object(
        auth_utils.helpers, 'get_execution_session', autospec=True)
    def test_get_client_session_without_trust_id(
            self, mock_get_execution_session, mock_get_token_client_session):
        mock_get_token_client_session.return_value = mock.sentinel.session
        mock_exec_session = mock.Mock(trust_id=None,
                                      token=mock.sentinel.token,
                                      project_id=mock.sentinel.project_id)

        session = auth_utils.get_client_session(
            execution_session=mock_exec_session, conf=mock.sentinel.conf)

        self.assertEqual(mock.sentinel.session, session)
        self.assertFalse(mock_get_execution_session.called)
        mock_get_token_client_session.assert_called_once_with(
            token=mock.sentinel.token, project_id=mock.sentinel.project_id)

    @mock.patch.object(auth_utils, '_get_session', autospec=True)
    @mock.patch.object(auth_utils, 'identity', autospec=True)
    @mock.patch.object(
        auth_utils.helpers, 'get_execution_session', autospec=True)
    def test_get_token_client_session(
            self, mock_get_execution_session, mock_identity,
            mock_get_session):
        cfg.CONF.set_override('www_authenticate_uri',
                              'foo_www_authenticate_uri/v2.0',
                              auth_utils.CFG_MURANO_AUTH_GROUP)

        mock_get_execution_session.return_value = \
            mock.Mock(token=mock.sentinel.token,
                      project_id=mock.sentinel.project_id)
        mock_identity.Token.return_value = mock.sentinel.auth
        mock_get_session.return_value = mock.sentinel.session

        session = auth_utils.get_token_client_session()
        self.assertEqual(mock.sentinel.session, session)

        mock_get_execution_session.assert_called_once_with()
        mock_identity.Token.assert_called_once_with(
            'foo_www_authenticate_uri/v3', token=mock.sentinel.token,
            project_id=mock.sentinel.project_id)
        mock_get_session.assert_called_once_with(
            auth=mock.sentinel.auth,
            conf_section=None)

    @mock.patch.object(auth_utils, 'get_token_client_session', autospec=True)
    @mock.patch.object(auth_utils, 'ks_client', autospec=True)
    def test_create_keystone_client(self, mock_ks_client,
                                    mock_get_token_client_session):
        mock_ks_client.Client.return_value = mock.sentinel.ks_client
        mock_session = mock.Mock(
            token=mock.sentinel.token, project_id=mock.sentinel.project_id,
            conf=mock.sentinel.conf)
        mock_get_token_client_session.return_value = mock_session

        ks_client = auth_utils.create_keystone_client(
            mock.sentinel.token, mock.sentinel.project_id, mock.sentinel.conf)

        self.assertEqual(mock.sentinel.ks_client, ks_client)
        mock_ks_client.Client.assert_called_once_with(session=mock_session)

    @mock.patch.object(auth_utils, 'create_keystone_client', autospec=True)
    @mock.patch.object(
        auth_utils, '_create_keystone_admin_client', autospec=True)
    def test_create_trust(self, mock_create_ks_admin_client,
                          mock_create_ks_client):
        mock_auth_ref = mock.Mock(user_id=mock.sentinel.trustor_user,
                                  project_id=mock.sentinel.project_id,
                                  role_names=mock.sentinel.role_names)
        mock_admin_session = mock.Mock(**{
            'auth.get_user_id.return_value': mock.sentinel.trustee_user
        })
        mock_user_session = mock.Mock(**{
            'auth.get_access.return_value': mock_auth_ref
        })
        mock_trust = mock.Mock(id=mock.sentinel.trust_id)
        mock_admin_client = mock.Mock(session=mock_admin_session)
        mock_user_client = mock.Mock(
            session=mock_user_session,
            **{'trusts.create.return_value': mock_trust})

        mock_create_ks_admin_client.return_value = mock_admin_client
        mock_create_ks_client.return_value = mock_user_client

        trust_id = auth_utils.create_trust(
            trustee_token=mock.sentinel.trustee_token,
            trustee_project_id=mock.sentinel.trustee_project_id)

        self.assertEqual(mock.sentinel.trust_id, trust_id)
        mock_create_ks_admin_client.assert_called_once_with()
        mock_create_ks_client.assert_called_once_with(
            token=mock.sentinel.trustee_token,
            project_id=mock.sentinel.trustee_project_id)
        mock_admin_client.session.auth.get_user_id.assert_called_once_with(
            mock_admin_session)
        mock_user_client.session.auth.get_access.assert_called_once_with(
            mock_user_session)
        mock_user_client.trusts.create.assert_called_once_with(
            trustor_user=mock.sentinel.trustor_user,
            trustee_user=mock.sentinel.trustee_user,
            impersonation=True,
            role_names=mock.sentinel.role_names,
            project=mock.sentinel.project_id)

    @mock.patch.object(auth_utils, 'create_keystone_client', autospec=True)
    def test_delete_trust(self, mock_ks_client):
        mock_auth_ref = mock.Mock(trust_id=mock.sentinel.trust_id,
                                  token=mock.sentinel.token,
                                  project_id=mock.sentinel.project_id)
        mock_user_session = mock.Mock(**{
            'auth.get_access.return_value': mock_auth_ref
        })
        mock_user_client = mock.Mock(
            session=mock_user_session)

        mock_ks_client.return_value = mock_user_client

        auth_utils.delete_trust(mock_auth_ref)

        mock_user_client.trusts.delete.assert_called_once_with(
            mock_auth_ref.trust_id)

    def test_get_config_option(self):
        cfg.CONF.set_override('url', 'foourl', 'murano')
        self.assertEqual('foourl', auth_utils._get_config_option(
            'murano', 'url'))

    def test_get_config_option_return_default(self):
        self.assertIsNone(auth_utils._get_config_option(None, 'url'))

    def test_get_session(self):
        mock_ka_loading = self._init_mock_cfg()

        session = auth_utils._get_session(mock.sentinel.auth)

        self.assertEqual(mock.sentinel.session, session)
        mock_ka_loading.load_session_from_conf_options.\
            assert_called_once_with(auth=mock.sentinel.auth,
                                    conf=cfg.CONF,
                                    group=auth_utils.CFG_MURANO_AUTH_GROUP)

    def test_get_session_client_parameters(self):

        cfg.CONF.set_override('url', 'foourl', 'murano')

        expected_result = {
            'session': mock.sentinel.session,
            'endpoint_override': 'foourl'
        }

        result = auth_utils.get_session_client_parameters(
            conf='murano',
            service_type=mock.sentinel.service_type,
            service_name=mock.sentinel.service_name,
            session=mock.sentinel.session)

        for key, val in expected_result.items():
            self.assertEqual(val, result[key])

    def test_get_session_client_parameters_without_url(self):
        cfg.CONF.set_override('home_region', 'fooregion')

        expected_result = {
            'session': mock.sentinel.session,
            'service_type': mock.sentinel.service_type,
            'service_name': mock.sentinel.service_name,
            'interface': mock.sentinel.endpoint_type,
            'region_name': 'fooregion'
        }

        result = auth_utils.get_session_client_parameters(
            service_type=mock.sentinel.service_type,
            service_name=mock.sentinel.service_name,
            interface=mock.sentinel.endpoint_type,
            session=mock.sentinel.session)

        for key, val in expected_result.items():
            self.assertEqual(val, result[key])

    @mock.patch.object(
        auth_utils, '_create_keystone_admin_client', autospec=True)
    def test_get_user(self, mock_create_ks_admin_client):
        mock_client = mock.Mock(
            **{'users.get.return_value.to_dict.return_value':
                mock.sentinel.user})
        mock_create_ks_admin_client.return_value = mock_client

        user = auth_utils.get_user(mock.sentinel.uid)

        self.assertEqual(mock.sentinel.user, user)
        mock_client.users.get.assert_called_once_with(mock.sentinel.uid)
        mock_client.users.get.return_value.to_dict.assert_called_once_with()

    @mock.patch.object(
        auth_utils, '_create_keystone_admin_client', autospec=True)
    def test_get_project(self, mock_create_ks_admin_client):
        mock_client = mock.Mock(
            **{'projects.get.return_value.to_dict.return_value':
                mock.sentinel.project})
        mock_create_ks_admin_client.return_value = mock_client

        project = auth_utils.get_project(mock.sentinel.pid)

        self.assertEqual(mock.sentinel.project, project)
        mock_client.projects.get.assert_called_once_with(mock.sentinel.pid)
        mock_client.projects.get.return_value.to_dict.assert_called_once_with()
