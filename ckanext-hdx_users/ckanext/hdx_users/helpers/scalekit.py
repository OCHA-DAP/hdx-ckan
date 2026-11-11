'''
Minimal Scalekit "Bring Your Own Auth" client over raw HTTP (no SDK).

Used by ckanext.hdx_users.views.mcp_auth to tell Scalekit which HDX user signed in
for a pending MCP login request. Pilot: the client_credentials token is not cached,
a new one is fetched for every login.
'''
import logging
from typing import Any
from urllib.parse import quote, urlencode

import requests

import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

TIMEOUT = 10
# How much of a Scalekit error response goes into the log
LOG_BODY_CHARS = 300


class ScalekitError(Exception):
    pass


def _body_for_log(resp: requests.Response) -> str:
    '''The start of a response body on one line, e.g. Scalekit's "invalid login request Id" message.'''
    return ' '.join((resp.text or '').split())[:LOG_BODY_CHARS]


def _cfg(key: str) -> str:
    value = tk.config.get(f'hdx.mcp_auth.{key}')
    if not value:
        raise RuntimeError(f'Missing config: hdx.mcp_auth.{key}')
    return value


def _env_url() -> str:
    return _cfg('scalekit_env_url').rstrip('/')


def _post(name: str, url: str, **kwargs: Any) -> dict[str, Any]:
    '''
    POSTs to Scalekit and returns the JSON object it sends back. Raises ScalekitError on
    anything else: a non-2xx status, a redirect (not followed) or a body that isn't a JSON object.
    '''
    resp = requests.post(url, timeout=TIMEOUT, allow_redirects=False, **kwargs)
    if not 200 <= resp.status_code < 300:
        log.error('Scalekit %s request failed: %s %s', name, resp.status_code, _body_for_log(resp))
        raise ScalekitError(f'Scalekit {name} request failed: {resp.status_code}')
    try:
        body = resp.json()
    except ValueError:
        body = None
    if not isinstance(body, dict):
        log.error('Scalekit %s request returned no JSON object: %s', name, _body_for_log(resp))
        raise ScalekitError(f'Scalekit {name} request returned no JSON object')
    return body


def _m2m_token() -> str:
    body = _post('token', f'{_env_url()}/oauth/token', data={
        'grant_type': 'client_credentials',
        'client_id': _cfg('scalekit_client_id'),
        'client_secret': _cfg('scalekit_client_secret'),
    })
    token = body.get('access_token')
    if not token:
        raise ScalekitError('Scalekit token response has no access_token')
    return token


def submit_user(login_request_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    '''
    Sends the signed-in user's details to the pending Scalekit auth request.
    Raises on any failure; the caller must not redirect back to Scalekit in that case.
    '''
    url = (
        f"{_env_url()}/api/v1/connections/{_cfg('scalekit_connection_id')}"
        f"/auth-requests/{quote(login_request_id, safe='')}/user"
    )
    result = _post('user-details', url, json=payload, headers={'Authorization': f'Bearer {_m2m_token()}'})
    if not result.get('auth_request_id'):
        # Scalekit docs say the response carries it. Pilot: only warn until a real
        # response confirms that (plan L4), then treat a missing ID as a failure.
        log.warning('Scalekit user-details response has no auth_request_id: lri=%s', login_request_id)
    return result


def callback_url(state: str) -> str:
    '''The Scalekit URL the browser goes back to after a successful submit_user().'''
    return (
        f"{_env_url()}/sso/v1/connections/{_cfg('scalekit_connection_id')}"
        f"/partner:callback?{urlencode({'state': state})}"
    )
