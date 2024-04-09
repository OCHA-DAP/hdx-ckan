# encoding: utf-8
import logging
from typing import Union, Any, Optional, Mapping

from flask import Blueprint

import ckan.authz as new_authz
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk
import ckan.model as model
import ckanext.hdx_users.helpers.helpers as usr_h
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_users.helpers.tokens as tokens
import ckanext.hdx_users.helpers.user_extra as ue_helpers

from ckan.common import session
from ckan.types import Response, Context
from ckan.views.user import PerformResetView, RequestResetView, rotate_token, next_page_or_default
from ckan.views.user import (
    follow as _follow, followers as _followers, unfollow as _unfollow, login as _login, logout as _logout
)
from ckanext.hdx_users.logic.first_login import FirstLoginLogic
# from ckan.views.user import generate_apikey as _generate_apikey
# from ckan.views.user import logged_out as _logged_out
from ckanext.hdx_users.views.user_edit_view import HDXEditView, HDXTwoStep
from ckanext.hdx_users.views.user_onboarding_view import HDXUserOnboardingView
from ckanext.hdx_users.views.user_view_helper import *


log = logging.getLogger(__name__)

render = tk.render
abort = tk.abort
get_action = tk.get_action
check_access = tk.check_access
request = tk.request
h = tk.h
_ = tk._
g = tk.g
config = tk.config
redirect = tk.redirect_to
current_user = tk.current_user
login_user = tk.login_user

NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError

User = model.User

user_onboarding_view = HDXUserOnboardingView()
user = Blueprint(u'hdx_user', __name__, url_prefix=u'/user')


class HDXRequestResetView(RequestResetView):
    def get(self):
        template_data = {
            'capcha_api_key': config.get('ckan.recaptcha.publickey')
        }
        return render('user/forgot_password.html', template_data)

    def post(self):
        """
        Email password reset instructions to user
        """
        context = {'model': model, 'session': model.Session, 'user': g.user,
                   'auth_user_obj': g.userobj}
        try:
            check_access('request_reset', context)
            usr_h.is_valid_captcha(request.form.get('g-recaptcha-response'))
        except NotAuthorized:
            abort(403, _('Unauthorized to request reset password.'))
        except ValidationError:
            return json.dumps(
                {'success': False, 'error': {'message': _(u'Bad Captcha. Please try again.')}})

        if request.method == 'POST':
            # user_id should be lowercase (for name and email)
            user_id = request.form.get('user').lower()

            context = {
                'model': model,
                'session': model.Session,
                'user': g.user
            }

            context_user_show = {
                'model': model,
                'user': g.user,
                'ignore_auth': True
            }

            user_obj = None
            try:
                data_dict = get_action('user_show')(context_user_show, {'id': user_id})
                user_obj = context_user_show['user_obj']
            except NotFound:
                # return OnbUserNotFound
                return OnbSuccess
            try:
                token = tokens.token_show(context, data_dict)
            except NotFound as e:
                token = {'valid': True}  # Until we figure out what to do with existing users
            except Exception as ex:
                # return OnbErr
                return OnbSuccess

            if not token['valid']:
                token = tokens.refresh_token(context, token)
                # redirect to validation page
                if user_obj and tokens.send_validation_email(
                    {'id': user_obj.id, 'email': user_obj.email},
                    token,
                    'Complete your HDX registration',
                    'email/content/onboarding_email_validation.html',
                    h.url_for('hdx_user_register.validate', token=token['token'], qualified=True)
                ):
                    return OnbSuccess
                # return OnbErr
                return OnbSuccess
            if user_obj:
                try:
                    # hdx_mailer.send_reset_link(user_obj)
                    get_action('hdx_send_reset_link')(context, {'id': user_id})
                    return OnbSuccess
                except hdx_mailer.MailerException as e:
                    # return OnbResetLinkErr
                    return OnbSuccess
        # return render('user/request_reset.html')
        return render('home/index.html')


class HDXPerformResetView(PerformResetView):

    def get(self, id):
        context = {
            u'model': model,
            u'session': model.Session,
            u'keep_email': True
        }

        g.reset_key = request.args.get(u'key')
        try:
            check_access(u'user_update', context, {
                'id': id,
                'reset_key': g.reset_key,
            })
        except NotAuthorized:
            msg = _(u'The link you accessed is either invalid or has expired. Please request another reset link. '
                    u'If the problem persists please '
                    u'<a href="/faq#auto-faq-Contact--a">contact us</a>.')
            h.flash(msg, category='alert-error')
            return h.redirect_to(u'hdx_user.request_reset')

        return render(u'user/perform_reset.html')

    def _get_form_password(self):
        password1 = request.form.get(u'password1')
        password2 = request.form.get(u'password2')
        if password1 is not None and password1 != u'':
            if password1 != password2:
                raise ValueError(_(u'The passwords you entered' u' do not match.'))
            return password1
        msg = _(u'You must provide a password')
        raise ValueError(msg)


def read(id=None):
    """
    Identical to user.py:read, but needs to be here to receive requests
    and direct them to the correct _setup_template_variables method
    """
    context = {u'model': model, u'session': model.Session,
               u'user': g.user, u'auth_user_obj': g.userobj,
               u'for_view': True}
    data_dict = {u'id': id,
                 u'user_obj': g.userobj,
                 u'include_datasets': True,
                 u'include_num_followers': True}

    try:
        check_access(u'user_show', context, data_dict)
    except NotAuthorized:
        abort(403, _(u'Not authorized to see this page'))

    context[u'with_related'] = True

    extra_vars = _extra_template_variables(context, data_dict)

    # The legacy templates have the user's activity stream on the user
    # profile page, new templates do not.
    # if tk.asbool(config.get(u'ckan.legacy_templates', False)):
    #     g.user_activity_stream = get_action(u'user_activity_list_html')(
    #         context, {u'id': g.user_dict[u'id']})

    return render(u'user/read.html', extra_vars=extra_vars)


def _extra_template_variables(context, data_dict):
    """
    Sets up template variables. If the user is deleted, throws a 404
    unless the user is logged in as sysadmin.

    This is no longer inspied from ckan's UserController -> _setup_template_variables()
    but from the new flask controller views/users -> _extra_template_variables()
    """
    is_sysadmin = new_authz.is_sysadmin(g.user)
    try:
        user_dict = get_action(u'user_show')(context, data_dict)
    except NotFound:
        abort(404, _(u'User not found'))
    except NotAuthorized:
        abort(403, _(u'Not authorized to see this page'))
    if user_dict[u'state'] == u'deleted' and not is_sysadmin:
        abort(404, _(u'User not found'))
    is_myself = user_dict[u'name'] == g.user
    about_formatted = h.render_markdown(user_dict[u'about'])

    extra = {
        u'is_sysadmin': is_sysadmin,
        u'user_dict': user_dict,
        u'is_myself': is_myself,
        u'about_formatted': about_formatted
    }
    return extra


def _authenticate(identity: 'Mapping[str, Any]') -> Optional["User"]:
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

def _check_email_validation(user_obj: "User") -> bool:
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

def login() -> Union[Response, str]:
    '''
    This is based on ckan.views.user.login() but with the following changes:
    - we added the first login logic
    - we skip the GET method, as we don't have a dedicated login page
    - we skip ckan.lib.authenticator.ckan_authenticator() as we want to fail if the user is not authenticated by
      ckanext.security
    - after a successful login, we check that the user validated their email
    '''

    extra_vars: dict[str, Any] = {}

    if current_user.is_authenticated:
        h.flash_notice(_('You are already logged in.'))
        return render("home/index.html", extra_vars)

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
                rotate_token()
                first_login_logic.mark_state_as_used_if_needed()
                session['from_login'] = True
                return next_page_or_default(next)
            else:
                login_user(user_obj)
                rotate_token()
                first_login_logic.mark_state_as_used_if_needed()
                session['from_login'] = True
                return next_page_or_default(next)
        else:
            err = _(u"Login failed. Bad username or password.")
            extra_vars = ue_helpers.get_login(False, err)
            extra_vars['data']['login_came_from'] = request.args.get('came_from')
            # h.flash_error(err)
            return render("home/index.html", extra_vars)

    return render("home/index.html", extra_vars)

def logged_out_page():
    template_data = ue_helpers.get_logout(True, _('User logged out with success'))
    return render('home/index.html', extra_vars=template_data)

user.add_url_rule(u'/reset', view_func=HDXRequestResetView.as_view(str(u'request_reset')))
user.add_url_rule(u'/reset/<id>', view_func=HDXPerformResetView.as_view(str(u'perform_reset')))

_edit_view = HDXEditView.as_view(str(u'edit'))
user.add_url_rule(u'/edit', view_func=_edit_view)
user.add_url_rule(u'/edit/<id>', view_func=_edit_view)

user.add_url_rule(u'/follow_details', view_func=user_onboarding_view.follow_details, methods=(u'POST',))
user.add_url_rule(u'/request_membership', view_func=user_onboarding_view.request_membership, methods=(u'POST',))
# user.add_url_rule(u'/request_new_organization', view_func=user_onboarding_view.request_new_organization,
#                   methods=(u'POST',))
user.add_url_rule(u'/invite_friends', view_func=user_onboarding_view.invite_friends, methods=(u'POST',))

user.add_url_rule(u'/logged_out_redirect', view_func=logged_out_page)
user.add_url_rule(u'/logged_out_page', view_func=logged_out_page)
# user.add_url_rule(u'/logged_in', view_func=hdx_auth_view.logged_in, methods=(u'GET', u'POST',))
user.add_url_rule(u'/login', view_func=login, methods=(u'POST', u'GET'))
user.add_url_rule(u'/_logout', view_func=_logout)
# user.add_url_rule(u'/logged_out', view_func=_logged_out)

user.add_url_rule(u'/follow/<id>', view_func=_follow, methods=(u'POST',))
user.add_url_rule(u'/unfollow/<id>', view_func=_unfollow, methods=(u'POST',))
user.add_url_rule(u'/followers/<id>', view_func=_followers)

# user.add_url_rule(u'/generate_key', view_func=_generate_apikey, methods=(u'POST',))

user.add_url_rule(u'/<id>', view_func=read)

user.add_url_rule('/configure_mfa/<id>', view_func=HDXTwoStep.configure_mfa, methods=['POST'])
user.add_url_rule('/configure_mfa/<id>/new', view_func=HDXTwoStep.new, methods=['GET', 'POST'])
user.add_url_rule('/configure_mfa/<id>/delete', view_func=HDXTwoStep.delete, methods=['GET'])
