'''
Scalekit "Bring Your Own Auth" login endpoint for the HDX MCP servers (pilot).

Scalekit dashboard > MCP Servers > HDX MCP > Configuration > Advanced Configuration:
    Login Endpoint URL = https://<hdx-host>/user/mcp-login

The pages live under /user/ because /mcp on the HDX host is routed to the mcp-hdx container.
They reuse the normal HDX login (hdx_signin.login) through `came_from` and are switched
on by `hdx.mcp_auth.enabled` (default false).
'''
import logging
import re
from collections.abc import Mapping

from flask import Blueprint, current_app, redirect

import ckan.plugins.toolkit as tk

from ckanext.hdx_users.helpers import scalekit

log = logging.getLogger(__name__)

request = tk.request
_ = tk._

hdx_mcp_auth = Blueprint('hdx_mcp_auth', __name__)

_LRI = re.compile(r'lri_[A-Za-z0-9_-]{1,128}')
_MAX_STATE = 2048


@hdx_mcp_auth.before_request
def _before_request():
    # CKAN then sends "Cache-Control: private", so no shared cache stores these
    # responses, including the 404 below
    request.environ['__no_cache__'] = True
    if not tk.config.get('hdx.mcp_auth.enabled'):
        tk.abort(404)


@hdx_mcp_auth.after_request
def _after_request(response):
    # One click on the confirm page binds the HDX account to an MCP login, so no site may frame it.
    # HDX's own X-Frame-Options (hdx_theme http_headers) is skipped when '/view/' appears anywhere in
    # the URL, query string included. It runs after this hook and may turn DENY into SAMEORIGIN,
    # which is still safe, and browsers apply frame-ancestors first.
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "frame-ancestors 'none'"
    return response


def _login_request_params(source: Mapping[str, str]) -> tuple[str, str]:
    lri = source.get('login_request_id', '')
    state = source.get('state', '')
    if not _LRI.fullmatch(lri) or not state or len(state) > _MAX_STATE:
        tk.abort(400, _('Invalid MCP login request'))
    return lri, state


def login():
    # The confirm page sends anonymous users on to the HDX login
    lri, state = _login_request_params(request.args)
    return tk.redirect_to('hdx_mcp_auth.confirm', login_request_id=lri, state=state)


def confirm():
    user = tk.current_user

    if request.method == 'GET':
        lri, state = _login_request_params(request.args)
        if not user.is_authenticated:
            return tk.redirect_to('hdx_signin.login', came_from=request.full_path)
        # Always shown, even to users who are already signed in: it stops a crafted
        # /user/mcp-login link from silently binding a victim's HDX account to someone
        # else's MCP client.
        return tk.render('user/mcp_confirm.html', extra_vars={
            'login_request_id': lri,
            'state': state,
            'user_display_name': user.display_name,
        })

    if not user.is_authenticated:
        tk.abort(401)
    # identify_user() already signs out inactive users; this is only a cheap guard
    if user.state != 'active':
        tk.abort(403)
    # Check the CSRF token here instead of relying on Flask-WTF's global hook. In CKAN 2.11,
    # ckan_before_request calls csrf.exempt() for every anonymous or API-token request, which
    # exempts the view for the rest of the process.
    current_app.extensions['csrf'].protect()
    lri, state = _login_request_params(request.form)

    payload = {
        'sub': user.id,
        'email': user.email,
        'name': user.display_name,
        # mcp-hdx needs the user's details in the access token (logging, Mixpanel). Scalekit copies custom
        # attributes into the token under `custom_claims`, but drops one named `email`, so they all use an
        # `hdx_` prefix. `hdx_email_hash` is CKAN's (md5 of the lower-cased email), the same value
        # user_show returns.
        'custom_attributes': {
            'hdx_name': user.display_name,
            'hdx_email': user.email,
            'hdx_email_hash': user.email_hash,
        },
    }
    try:
        result = scalekit.submit_user(lri, payload)
    except Exception as e:
        if isinstance(e, scalekit.ScalekitError):
            # Expected (Scalekit unreachable or refusing): one line with the reason, no traceback
            log.warning('MCP login failed: lri=%s user=%s: %s', lri, user.id, e)
        else:
            log.exception('MCP login failed: lri=%s user=%s', lri, user.id)
        # Scalekit docs: never redirect back to Scalekit when this call fails
        tk.abort(502, _('Could not complete the sign-in. Please start again from your AI assistant.'))

    # WARNING (like hdx_signin.login) so the line reaches the stage logs
    log.warning('MCP login succeeded: lri=%s user=%s scalekit_auth_request=%s',
                lri, user.id, result.get('auth_request_id'))
    return redirect(scalekit.callback_url(state))


hdx_mcp_auth.add_url_rule('/user/mcp-login', view_func=login)
hdx_mcp_auth.add_url_rule('/user/mcp-confirm', view_func=confirm, methods=('GET', 'POST'))
