import pytest

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
import ckan.tests.helpers as helpers


@pytest.mark.usefixtures(u"clean_db")
class TestApiToken(object):
    LIMIT = 180  # days

    def test_token_expiry(self):
        user = factories.User()
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
