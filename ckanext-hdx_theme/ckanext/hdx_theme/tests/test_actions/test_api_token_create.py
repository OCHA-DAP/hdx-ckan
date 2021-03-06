import pytest

from builtins import str

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers


@pytest.fixture(scope='module')
def keep_db_tables_on_clean():
    model.repo.tables_created_and_initialised = True


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db')
class TestApiToken(object):
    LIMIT = 180  # days

    def test_token_expiry_with_integer_params(self):
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

    def test_token_expiry_with_str_params(self):
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
