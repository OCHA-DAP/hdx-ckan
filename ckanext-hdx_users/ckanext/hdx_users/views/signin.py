from typing import Union, Any, Optional, Mapping
from urllib.parse import quote

from flask import Blueprint, Response

from ckan.common import session
from ckan.types import Context
from ckan.views.user import logout as _logout, rotate_token, next_page_or_default
from ckanext.hdx_users.logic.first_login import FirstLoginLogic

import json
import ckan.plugins.toolkit as tk
import ckan.plugins as plugins
import ckan.model as model

import ckanext.hdx_users.helpers.tokens as tokens


hdx_signin = Blueprint(u'hdx_signin', __name__, url_prefix=u'/')

abort = tk.abort
render = tk.render
request = tk.request
h = tk.h
_ = tk._
current_user = tk.current_user
login_user = tk.login_user

NotFound = tk.ObjectNotFound


def _authenticate(identity: 'Mapping[str, Any]') -> Optional[model.User]:
    '''
    This is based on ckan.lib.authenticator.ckan_authenticator() but with the following changes:
    - we don't fall back to ckan.lib.authenticator.default_authenticator() if the user is not authenticated by
      ckanext.security

    Please note that ckanext.security does use ckan.lib.authenticator.default_authenticator() as part of its internal
    logic.
    '''
    for item in plugins.PluginImplementations(plugins.IAuthenticator):
        user_obj = item.authenticate(identity)
        if user_obj:
            return user_obj
    return None


def _check_email_validation(user_obj: model.User) -> bool:
    user_id = user_obj.id
    try:
        token = tokens.token_show({}, {'id': user_id})
    except NotFound as e:
        token = {'valid': True}  # Until we figure out what to do with existing users
    except:
        abort(500, _('Something wrong'))
    if not token['valid']:
        return False
    return True

def _remember_user_for_next_signin(res: Response, user_obj: model.User):
    login_dict = {
        'display_name': user_obj.display_name,
        'email': user_obj.email,
        'email_hash': user_obj.email_hash,
        'login': user_obj.name
    }
    max_age = int(14 * 24 * 3600)
    res.set_cookie('hdx_login', quote(json.dumps(login_dict)), max_age=max_age, secure=True)

def login() -> Union[Response, str]:
    '''
    This is based on ckan.views.user.login() but with the following changes:
    - we added the first login logic
    - we skip the GET method, as we don't have a dedicated login page
    - we skip ckan.lib.authenticator.ckan_authenticator() as we want to fail if the user is not authenticated by
      ckanext.security
    - after a successful login, we check that the user validated their email
    '''

    extra_vars: dict[str, Any] = {
        'data': {
            'login_came_from': request.args.get('came_from')
        },
    }

    if current_user.is_authenticated:
        h.flash_notice(_('You are already logged in.'))
        return tk.redirect_to('hdx_splash.index')

    if request.method == "POST":
        username_or_email = request.form.get("login")
        password = request.form.get("password")
        _remember = request.form.get("remember")

        identity = {
            u"login": username_or_email,
            u"password": password
        }

        user_obj = _authenticate(identity)

        if user_obj:
            validated_email = _check_email_validation(user_obj)
            if not validated_email:
                _logout()
                h.flash_error(_('You have not yet validated your email.'))
                return h.redirect_to('hdx_splash.index')

        if user_obj:
            first_login_context: Context = {
                'model': model,
                'session': model.Session,
                'user': user_obj.name, 'auth_user_obj': user_obj
            }
            first_login_logic = FirstLoginLogic(first_login_context, user_obj.id)
            first_login_url = first_login_logic.determine_initial_redirect()
            next = first_login_url or request.args.get('next', request.args.get('came_from'))
            if _remember:
                from datetime import timedelta
                duration_time = timedelta(milliseconds=int(_remember))
                login_user(user_obj, remember=True, duration=duration_time)
                # rotate_token()
                # first_login_logic.mark_state_as_used_if_needed()
                # session['from_login'] = True
                # return next_page_or_default(next)
            else:
                login_user(user_obj)
            rotate_token()
            first_login_logic.mark_state_as_used_if_needed()
            session['from_login'] = True
            res = next_page_or_default(next)
            _remember_user_for_next_signin(res, user_obj)
            return res
        else:
            extra_vars['error_message'] = _(u"Login failed. Bad username or password.")
            return render("user/signin.html", extra_vars=extra_vars)

    info_message_type = request.args.get('info_message_type')
    if info_message_type:
        info_message = h.HDX_CONST('UI_CONSTANTS')['SIGNIN'].get(info_message_type)
        extra_vars['info_message'] = info_message
    return render('user/signin.html', extra_vars=extra_vars)


hdx_signin.add_url_rule(u'/sign-in/', view_func=login, strict_slashes=False, methods=('GET', 'POST'))
hdx_signin.add_url_rule(u'/login/', view_func=login, strict_slashes=False, methods=('GET', 'POST'))
hdx_signin.add_url_rule(u'/user/login/', view_func=login, strict_slashes=False, methods=('GET', 'POST'))
