import pytest
import mock

from builtins import str

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db')
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
