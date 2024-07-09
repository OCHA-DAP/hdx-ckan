import mock
import pytest
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from collections import OrderedDict

_get_action = tk.get_action
h = tk.h
ValidationError = tk.ValidationError

USER = 'onboarding_test_user'
USER_EMAIL = 'onboarding_test_user@test.org'
USER_NEW_EMAIL = 'onboarding_new_test_user@test.org'

TOKEN = OrderedDict([('id', 'old_token_id'), ('user_id', USER), ('token', 'old_token'), ('valid', False)])
NEW_TOKEN = OrderedDict([('id', 'new_token_id'), ('user_id', USER), ('token', 'new_token'), ('valid', False)])


@pytest.fixture()
def setup_data():
    factories.User(name=USER, email=USER_EMAIL, fullname='Test User')


@pytest.mark.usefixtures('clean_db', 'clean_index', 'setup_data')
class TestOnboardingChangeEmail(object):

    @mock.patch('ckanext.hdx_users.views.onboarding._user_can_change_email')
    @mock.patch('ckanext.hdx_users.helpers.tokens.is_user_validated_and_token_disabled', return_value=False)
    def test_page_loads_with_session(self, mock_is_user_validated, mock_user_can_change_email, app):
        user = model.User.by_name(USER)
        mock_user_can_change_email.return_value = user.id

        url = h.url_for('hdx_user_onboarding.change_email')
        response = app.get(url, status=200)
        assert response.status_code == 200, 'Page should load when user session is set'

    @mock.patch('ckanext.hdx_users.views.onboarding._user_can_change_email', return_value=None)
    def test_page_does_not_load_without_session(self, mock_user_can_change_email, app):
        url = h.url_for('hdx_user_onboarding.change_email')
        response = app.get(url, status=404)
        assert response.status_code == 404, 'Page should not load when user session is not set'

    @mock.patch('ckanext.hdx_users.views.onboarding._user_can_change_email')
    @mock.patch('ckanext.hdx_users.helpers.tokens.is_user_validated_and_token_disabled', return_value=True)
    def test_redirect_if_user_validated(self, mock_is_user_validated, mock_user_can_change_email, app):
        user = model.User.by_name(USER)
        mock_user_can_change_email.return_value = user.id

        url = h.url_for('hdx_user_onboarding.change_email')
        response = app.get(url)
        assert f'/signup/validated-account/{user.id}/' in response.request.path, 'User should be redirected if their account is validated'

    @mock.patch('ckanext.hdx_users.views.onboarding._user_can_change_email')
    @mock.patch('ckanext.hdx_users.helpers.tokens.is_user_validated_and_token_disabled', return_value=False)
    @mock.patch('ckanext.hdx_users.helpers.tokens.token_show', return_value=TOKEN)
    @mock.patch('ckanext.hdx_users.helpers.tokens.refresh_token', return_value=NEW_TOKEN)
    @mock.patch('ckanext.hdx_users.helpers.tokens.send_validation_email')
    def test_email_change_post_request(self, mock_send_validation_email, mock_refresh_token, mock_token_show, mock_is_user_validated, mock_user_can_change_email, app):
        user = model.User.by_name(USER)
        mock_user_can_change_email.return_value = user.id

        url = h.url_for('hdx_user_onboarding.change_email')
        data_dict = {
            'email': USER_NEW_EMAIL,
            'email2': USER_NEW_EMAIL,
        }
        app.post(url, data=data_dict)

        context = {
            'model': model,
            'user': USER,
            'keep_email': True,
        }
        updated_user_dict = _get_action('user_show')(context, {'id': user.id})
        assert updated_user_dict.get('email') == USER_NEW_EMAIL, 'User email should be updated'

        token = mock_send_validation_email.call_args[0][1]['token']
        assert token == 'new_token', 'New token should be sent in the validation email'

    @mock.patch('ckanext.hdx_users.views.onboarding._user_can_change_email')
    @mock.patch('ckanext.hdx_users.helpers.tokens.is_user_validated_and_token_disabled', return_value=False)
    def test_email_mismatch_post_request(self, mock_is_user_validated, mock_user_can_change_email, user, app):
        user = model.User.by_name(USER)
        mock_user_can_change_email.return_value = user.id

        url = h.url_for('hdx_user_onboarding.change_email')
        data_dict = {
            'email': USER_NEW_EMAIL,
            'email2': USER_EMAIL,
        }
        response = app.post(url, data=data_dict)
        assert 'The emails you entered do not match' in response.body, 'User should see an error message when emails do not match'
