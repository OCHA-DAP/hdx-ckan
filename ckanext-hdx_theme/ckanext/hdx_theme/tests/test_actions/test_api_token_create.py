import re

import pytest
import mock

from builtins import str

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers

h = tk.h


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db')
class TestApiToken(object):
    LIMIT = 365  # days
    ADMIN_LIMIT = 180

    @mock.patch('ckanext.hdx_theme.plugin.send_email_on_token_creation')
    def test_token_expiry_with_integer_params(self, send_email_helper_mock):
        user = factories.User(name='testuser1')
        context = {
            u"model": model,
            u"user": user[u"name"]
        }

        # should raise an exception when trying to create a token with expiration period > LIMIT
        with pytest.raises(tk.ValidationError):
            helpers.call_action(u"api_token_create", context=context,
                                user=user[u"name"], name=u"token-name",
                                expires_in=self.LIMIT + 1, unit=24 * 60 * 60)

        # there should be no problem creating a token with expiration period <= LIMIT
        helpers.call_action(u"api_token_create", context=context, user=user[u"name"], name=u"token-name",
                            expires_in=self.LIMIT, unit=24 * 60 * 60)

        sysadmin = factories.User(name='sysadmin1', sysadmin=True)
        context_sysadmin = {
            u"model": model,
            u"user": sysadmin[u"name"]
        }

        # should raise an exception when trying to create a token with expiration period > LIMIT
        with pytest.raises(tk.ValidationError):
            helpers.call_action(u"api_token_create", context=context_sysadmin,
                                user=sysadmin[u"name"], name=u"token-name",
                                expires_in=self.ADMIN_LIMIT + 1, unit=24 * 60 * 60)

        # there should be no problem creating a token with expiration period <= LIMIT
        helpers.call_action(u"api_token_create", context=context_sysadmin, user=sysadmin[u"name"], name=u"token-name",
                            expires_in=self.ADMIN_LIMIT, unit=24 * 60 * 60)

    @mock.patch('ckanext.hdx_theme.plugin.send_email_on_token_creation')
    def test_token_expiry_with_str_params(self, send_email_helper_mock):
        user = factories.User(name='testuser2')
        context = {
            u"model": model,
            u"user": user[u"name"]
        }

        # should raise an exception when trying to create a token with expiration period > LIMIT
        with pytest.raises(tk.ValidationError):
            helpers.call_action(u"api_token_create", context=context,
                                user=user[u"name"], name=u"token-name",
                                expires_in=str(self.LIMIT + 1), unit=str(24 * 60 * 60))

        # there should be no problem creating a token with expiration period <= LIMIT
        helpers.call_action(u"api_token_create", context=context, user=user[u"name"], name=u"token-name",
                            expires_in=str(self.LIMIT), unit=str(24 * 60 * 60))

    @mock.patch('ckanext.hdx_theme.plugin.send_email_on_token_creation')
    def test_api_tokens_page_access(self, send_email_helper_mock, app):
        factories.User(name='testuser3')
        factories.User(name='testuser4')
        factories.User(name='sysadmin3', sysadmin=True)
        owner_token = factories.APIToken(user='testuser3', name='owner-token', expires_in=2, unit=60 * 60)['token']
        other_token = factories.APIToken(user='testuser4', expires_in=2, unit=60 * 60)['token']
        sysadmin_token = factories.APIToken(user='sysadmin3', expires_in=2, unit=60 * 60)['token']
        url = h.url_for('user.api_tokens', id='testuser3')

        res = app.get(url, headers={'Authorization': owner_token})
        assert res.status_code == 200
        assert 'owner-token' in res.body
        assert 'c-page-header' not in res.body

        res = app.get(url, headers={'Authorization': sysadmin_token})
        assert res.status_code == 200
        assert 'owner-token' in res.body
        assert 'c-page-header' in res.body

        res = app.get(url, headers={'Authorization': other_token})
        assert res.status_code == 403

    @mock.patch('ckanext.hdx_theme.plugin.send_email_on_token_creation')
    def test_api_token_create_view(self, send_email_helper_mock, app):
        factories.User(name='testuser5')
        auth = {'Authorization': factories.APIToken(user='testuser5', expires_in=2, unit=60 * 60)['token']}
        url = h.url_for('user.api_tokens', id='testuser5')
        client = app.test_client()

        res = client.post(url, data={'name': 'created-in-ui', 'expires_in': '2', 'unit': '3600'},
                          headers=auth, follow_redirects=False)
        assert res.status_code == 302
        assert res.headers['Location'].endswith(url)

        res = client.get(url, headers=auth)
        assert res.status_code == 200
        token = re.search(r'class="hdx-v2-api-token-created__token">([^<]+)</span>', res.body).group(1)
        assert 'data-copy-value="{}"'.format(token) in res.body
        assert 'copy-into-buffer' not in res.body
        assert 'created-in-ui' in res.body

    @mock.patch('ckanext.hdx_theme.plugin.send_email_on_token_creation')
    def test_api_token_create_view_over_limit(self, send_email_helper_mock, app):
        factories.User(name='testuser6')
        auth = {'Authorization': factories.APIToken(user='testuser6', expires_in=2, unit=60 * 60)['token']}
        url = h.url_for('user.api_tokens', id='testuser6')

        res = app.post(url, data={'name': 'too-long', 'expires_in': str(self.LIMIT * 24 + 1), 'unit': '3600'},
                       headers=auth)
        assert res.status_code == 200
        assert 'Token needs to expire in maximum {} days'.format(self.LIMIT) in res.body
        assert re.search(r'<option value="3600"\s+selected', res.body)

    @mock.patch('ckanext.hdx_theme.plugin.send_email_on_token_creation')
    def test_api_tokens_unknown_user(self, send_email_helper_mock, app):
        factories.User(name='sysadmin4', sysadmin=True)
        auth = {'Authorization': factories.APIToken(user='sysadmin4', expires_in=2, unit=60 * 60)['token']}
        url = h.url_for('user.api_tokens', id='unknown-api-tokens-user')

        res = app.get(url, headers=auth)
        assert res.status_code == 404

        res = app.post(url, data={'name': 'token-name', 'expires_in': '2', 'unit': '3600'}, headers=auth)
        assert res.status_code == 404
