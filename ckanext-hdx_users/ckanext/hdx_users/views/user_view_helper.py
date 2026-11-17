import functools
import json
from collections.abc import Callable
from typing import Any

from flask import current_app, g

import ckan.lib.navl.dictization_functions as dictization_functions
from ckan.plugins import toolkit as tk

_ = tk._
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
DataError = dictization_functions.DataError
CaptchaNotValid = _('Captcha is not valid')
OnbCaptchaErr = json.dumps({'success': False, 'error': {'message': CaptchaNotValid}})
OnbNotAuth = json.dumps({'success': False, 'error': {'message': _('Unauthorized to create user')}})
OnbTokenNotFound = json.dumps({'success': False, 'error': {'message': 'Token not found'}})
OnbIntegrityErr = json.dumps({'success': False, 'error': {'message': 'Integrity Error'}})
OnbSuccess = json.dumps({'success': True})
OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbExistingUsername = json.dumps({'success': False, 'error': {'message': 'Username is already used'}})
OnbErr = json.dumps({'success': False, 'error': {'message': _('Something went wrong. Please contact support.')}})
OnbResetLinkErr = json.dumps({'success': False, 'error': {'message': _('Could not send reset link.')}})


def error_message(error_summary):
    return json.dumps({'success': False, 'error': {'message': error_summary}})


def enforce_csrf(view: Callable[..., Any]) -> Callable[..., Any]:
    '''
    Checks the CSRF token even when CKAN core exempted the request from the check.

    Core skips CSRF for requests "logged in via the Authorization header" (``ckan_before_request()`` in
    ``ckan/config/middleware/flask_app.py``). Flask-Login calls that loader for every request without a
    session user, so every anonymous request is exempt. Core's fix for GHSA-3h7g-fpc6-9vc9 keeps the
    check only for core's ``user.login`` and ``user.register``. Use this decorator on HDX views that log a
    user in or create or change an account (HDX-11757).
    '''
    @functools.wraps(view)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        app_config = current_app.config
        # g.csrf_valid is set by Flask-WTF when its own before_request check passed
        if app_config.get('WTF_CSRF_ENABLED') and app_config.get('WTF_CSRF_CHECK_DEFAULT') \
                and not g.get('csrf_valid'):
            # skips methods not in WTF_CSRF_METHODS; raises CSRFError (400) on a missing or bad token
            current_app.extensions['csrf'].protect()
        return view(*args, **kwargs)

    return wrapper
