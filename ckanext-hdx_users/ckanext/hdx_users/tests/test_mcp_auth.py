'''
Tests for the Scalekit "Bring Your Own Auth" MCP login pages: /user/mcp-login and /user/mcp-confirm
(ckanext.hdx_users.views.mcp_auth). Scalekit itself is mocked.

Signed-in requests use an API token in the Authorization header. Like other HDX view tests that sign in
this way, these tests don't use the `with_request_context` fixture: it shares Flask's `g` with the test
requests, so Flask-Login would keep serving the anonymous user cached during setup.

CKAN exempts API-token requests from Flask-WTF's global CSRF check, but the confirm POST checks the
token itself. So each POST first loads the confirm page with the same client (which keeps the session
cookie) and sends back the CSRF token from the form.
'''
import hashlib
import json
import re
from urllib.parse import parse_qs, urlparse

import mock
import pytest

import ckan.plugins.toolkit as tk
import ckan.tests.factories as factories
from ckan.tests.helpers import CKANTestApp

ENV_URL = 'https://scalekit.example.test'
CLIENT_ID = 'test-client-id'
CLIENT_SECRET = 'test-client-secret'
CONNECTION_ID = 'conn_test123'
LRI = 'lri_86659065219908156'
# Characters a Scalekit state may contain. It must reach Scalekit's callback unchanged.
STATE = 'HntJ_ENB6y+a/b=c-d.e~f'

SCALEKIT_REQUESTS = 'ckanext.hdx_users.helpers.scalekit.requests'

USER_NAME = 'mcp_auth_user'
USER_EMAIL = 'mcp_auth_user@hdx.hdxtest.org'
USER_FULLNAME = 'Mcp Auth User'


def _login_request():
    return {'login_request_id': LRI, 'state': STATE}


def _fake_response(status_code, payload=None, json_body=True):
    resp = mock.MagicMock()
    resp.status_code = status_code
    if json_body:
        resp.json.return_value = {} if payload is None else payload
        resp.text = json.dumps(resp.json.return_value)
    else:
        resp.json.side_effect = ValueError('No JSON object could be decoded')
        resp.text = '<html>\n  <body>Not JSON</body>\n</html>'
    return resp


def _token_response():
    return _fake_response(200, {'access_token': 'm2m-token', 'token_type': 'Bearer', 'expires_in': 3600})


def _confirm_form(client, headers):
    '''Loads the confirm page and returns its form fields, including the CSRF token.'''
    res = client.get('/user/mcp-confirm', query_string=_login_request(), headers=headers)
    assert res.status_code == 200
    field = tk.config.get('WTF_CSRF_FIELD_NAME')
    match = re.search(rf'name="{field}" value="([^"]+)"', res.body)
    assert match, 'the confirm page must contain the CSRF token'
    return dict(_login_request(), **{field: match.group(1)})


def _continue(app, headers, scalekit_responses):
    '''Clicks Continue on the confirm page, with Scalekit answering `scalekit_responses` in order.'''
    client = app.test_client()
    data = _confirm_form(client, headers)
    with mock.patch(SCALEKIT_REQUESTS) as fake_requests:
        fake_requests.post.side_effect = scalekit_responses
        res = client.post('/user/mcp-confirm', data=data, headers=headers, follow_redirects=False)
    return res, fake_requests.post


@pytest.fixture()
def signed_in_user():
    user = factories.User(name=USER_NAME, email=USER_EMAIL, fullname=USER_FULLNAME)
    token = factories.APIToken(user=USER_NAME, expires_in=2, unit=60 * 60)['token']
    return {'id': user['id'], 'headers': {'Authorization': token}}


@pytest.mark.usefixtures('hdx_clean_db')
def test_routes_are_disabled_by_default(app: CKANTestApp):
    for url in ('/user/mcp-login', '/user/mcp-confirm'):
        res = app.get(url, query_string=_login_request(), status=404)
        assert 'private' in res.headers.get('Cache-Control', ''), 'a CDN must not keep the 404'


@pytest.mark.usefixtures('hdx_clean_db')
@pytest.mark.ckan_config('hdx.mcp_auth.enabled', True)
@pytest.mark.ckan_config('hdx.mcp_auth.scalekit_env_url', ENV_URL)
@pytest.mark.ckan_config('hdx.mcp_auth.scalekit_client_id', CLIENT_ID)
@pytest.mark.ckan_config('hdx.mcp_auth.scalekit_client_secret', CLIENT_SECRET)
@pytest.mark.ckan_config('hdx.mcp_auth.scalekit_connection_id', CONNECTION_ID)
class TestMcpAuth:

    @pytest.mark.parametrize('query', [
        {},
        {'login_request_id': LRI},
        {'state': STATE},
        {'login_request_id': 'not-an-lri', 'state': STATE},
        {'login_request_id': 'lri_bad/../id', 'state': STATE},
        {'login_request_id': f'{LRI}\n', 'state': STATE},
        {'login_request_id': LRI, 'state': 'x' * 2049},
    ])
    def test_invalid_login_request_returns_400(self, app: CKANTestApp, query):
        # A 400 (not a "user not found" 404) also shows that /user/<id> doesn't capture these routes
        app.get('/user/mcp-login', query_string=query, status=400)
        app.get('/user/mcp-confirm', query_string=query, status=400)

    def test_mcp_login_goes_to_confirm_page(self, app: CKANTestApp):
        res = app.get('/user/mcp-login', query_string=_login_request(), follow_redirects=False)

        assert res.status_code == 302
        assert 'private' in res.headers.get('Cache-Control', '')
        location = urlparse(res.headers['Location'])
        assert location.path == '/user/mcp-confirm'
        assert parse_qs(location.query) == {'login_request_id': [LRI], 'state': [STATE]}

    def test_anonymous_user_is_sent_to_hdx_login(self, app: CKANTestApp):
        res = app.get('/user/mcp-confirm', query_string=_login_request(), follow_redirects=False)

        assert res.status_code == 302
        assert 'private' in res.headers.get('Cache-Control', '')
        location = urlparse(res.headers['Location'])
        with app.flask_app.test_request_context():
            login_path = urlparse(tk.url_for('hdx_signin.login')).path
        assert location.path == login_path

        came_from = urlparse(parse_qs(location.query)['came_from'][0])
        assert not came_from.scheme and not came_from.netloc, 'came_from must be local for the HDX login'
        assert came_from.path == '/user/mcp-confirm'
        assert parse_qs(came_from.query) == {'login_request_id': [LRI], 'state': [STATE]}

    def test_confirm_page_shows_user_and_login_request(self, app: CKANTestApp, signed_in_user):
        res = app.get('/user/mcp-confirm', query_string=_login_request(), headers=signed_in_user['headers'])

        assert res.status_code == 200
        assert USER_FULLNAME in res.body
        assert f'name="login_request_id" value="{LRI}"' in res.body
        assert f'name="state" value="{STATE}"' in res.body
        # The last referrer policy wins, and base.html sets "always": login_request_id and state
        # must not leak to other sites (Google Fonts, analytics)
        policies = re.findall(r'<meta name="referrer" content="([^"]+)"', res.body)
        assert policies[-1] == 'same-origin'

    def test_continue_sends_user_to_scalekit_and_redirects_to_callback(self, app: CKANTestApp, signed_in_user):
        user_resp = _fake_response(200, {'auth_request_id': 'req_123'})
        res, fake_post = _continue(app, signed_in_user['headers'], [_token_response(), user_resp])

        assert res.status_code == 302
        location = urlparse(res.headers['Location'])
        assert f'{location.scheme}://{location.netloc}{location.path}' == \
               f'{ENV_URL}/sso/v1/connections/{CONNECTION_ID}/partner:callback'
        assert parse_qs(location.query) == {'state': [STATE]}

        assert len(fake_post.call_args_list) == 2
        # (args, kwargs) unpacking works with every version of the mock package
        (token_url,), token_kwargs = fake_post.call_args_list[0]
        (user_url,), user_kwargs = fake_post.call_args_list[1]
        assert token_url == f'{ENV_URL}/oauth/token'
        assert token_kwargs['data'] == {
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
        }
        assert user_url == f'{ENV_URL}/api/v1/connections/{CONNECTION_ID}/auth-requests/{LRI}/user'
        assert user_kwargs['headers'] == {'Authorization': 'Bearer m2m-token'}
        assert user_kwargs['json'] == {
            'sub': signed_in_user['id'],
            'email': USER_EMAIL,
            'name': USER_FULLNAME,
            'custom_attributes': {'email': USER_EMAIL, 'email_hash': hashlib.md5(USER_EMAIL.encode()).hexdigest()},
        }
        assert token_kwargs['allow_redirects'] is False and user_kwargs['allow_redirects'] is False

    def test_post_without_csrf_token_is_rejected(self, app: CKANTestApp, signed_in_user):
        # CKAN 2.11 exempts the view from the global CSRF check after an anonymous request
        # (and for every API-token request), so this checks the view's own CSRF check.
        app.get('/user/mcp-confirm', query_string=_login_request(), follow_redirects=False)
        with mock.patch(SCALEKIT_REQUESTS) as fake_requests:
            res = app.post('/user/mcp-confirm', data=_login_request(), headers=signed_in_user['headers'],
                           follow_redirects=False)

        assert res.status_code == 400
        assert not fake_requests.post.called

    def test_anonymous_post_is_rejected(self, app: CKANTestApp):
        with mock.patch(SCALEKIT_REQUESTS) as fake_requests:
            res = app.post('/user/mcp-confirm', data=_login_request(), follow_redirects=False)

        assert res.status_code == 401
        assert not fake_requests.post.called

    @pytest.mark.parametrize('scalekit_responses', [
        pytest.param([_fake_response(401)], id='token-request-rejected'),
        pytest.param([_fake_response(200, {'token_type': 'Bearer'})], id='token-missing'),
        pytest.param([_token_response(), _fake_response(500)], id='user-details-error'),
        pytest.param([_token_response(), _fake_response(302)], id='user-details-redirect'),
        pytest.param([_token_response(), _fake_response(200, json_body=False)], id='user-details-not-json'),
        pytest.param([_token_response(), _fake_response(200, {})], id='user-details-no-auth-request-id'),
    ])
    def test_scalekit_failure_shows_error_and_does_not_redirect(self, app: CKANTestApp, signed_in_user,
                                                                 scalekit_responses):
        res, fake_post = _continue(app, signed_in_user['headers'], scalekit_responses)

        assert res.status_code == 502
        assert 'Location' not in res.headers
        assert len(fake_post.call_args_list) == len(scalekit_responses)

    def test_scalekit_error_message_is_logged(self, app: CKANTestApp, signed_in_user):
        # The real response Scalekit sends for an unknown login request
        user_resp = _fake_response(400, {'code': 3, 'message': 'invalid login request Id'})
        with mock.patch('ckanext.hdx_users.helpers.scalekit.log') as fake_log:
            res, _ = _continue(app, signed_in_user['headers'], [_token_response(), user_resp])

        assert res.status_code == 502
        logged = fake_log.error.call_args[0][0] % fake_log.error.call_args[0][1:]
        assert logged.startswith('Scalekit user-details request failed: 400')
        assert 'invalid login request Id' in logged

    def test_missing_config_shows_error_without_calling_scalekit(self, app: CKANTestApp, signed_in_user,
                                                                  ckan_config, monkeypatch):
        monkeypatch.setitem(ckan_config, 'hdx.mcp_auth.scalekit_client_secret', '')
        res, fake_post = _continue(app, signed_in_user['headers'], [])

        assert res.status_code == 502
        assert 'Location' not in res.headers
        assert not fake_post.called
