# encoding: utf-8
import logging

from flask import Blueprint

import ckan.authz as new_authz
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.helpers as usr_h
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_users.helpers.tokens as tokens
from ckan.views.user import PerformResetView
from ckan.views.user import RequestResetView
from ckan.views.user import follow as _follow
from ckan.views.user import followers as _followers
from ckan.views.user import generate_apikey as _generate_apikey
from ckan.views.user import logged_out as _logged_out
from ckan.views.user import login as _login
from ckan.views.user import logout as _logout
from ckan.views.user import unfollow as _unfollow
from ckanext.hdx_users.views.user_auth_view import HDXUserAuthView
from ckanext.hdx_users.views.user_edit_view import HDXEditView
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

NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError

hdx_auth_view = HDXUserAuthView()
user_onboarding_view = HDXUserOnboardingView()
user = Blueprint(u'hdx_user', __name__, url_prefix=u'/user')

hdx_login_link = Blueprint(u'hdx_login_link', __name__)


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

            context = {'model': model,
                       'user': g.user}

            user_obj = None
            try:
                data_dict = get_action('user_show')(context, {'id': user_id})
                user_obj = context['user_obj']
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
                # redirect to validation page
                if user_obj and tokens.send_validation_email({'id': user_obj.id, 'email': user_obj.email}, token):
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
                    u'<a href="/faq#auto-faq-Contact-How_do_I_contact_the_HDX_team_-a">contact us</a>.')
            h.flash(msg, category='alert-error', allow_html=True)
            return h.redirect_to(u'hdx_user.request_reset')

        try:
            user_dict = get_action(u'user_show')(context, {u'id': id})
        except NotFound:
            abort(404, _(u'User not found'))

        return render(u'user/perform_reset.html', {
            u'user_dict': user_dict
        })


def read(id=None):
    """
    Identical to user.py:read, but needs to be here to receive requests
    and direct them to the correct _setup_template_variables method
    """
    context = {u'model': model, u'session': model.Session,
               u'user': g.user or g.author, u'auth_user_obj': g.userobj,
               u'for_view': True}
    data_dict = {u'id': id,
                 u'user_obj': g.userobj,
                 u'include_datasets': True,
                 u'include_num_followers': True}

    context[u'with_related'] = True

    extra_vars = _extra_template_variables(context, data_dict)

    # The legacy templates have the user's activity stream on the user
    # profile page, new templates do not.
    if tk.asbool(config.get(u'ckan.legacy_templates', False)):
        g.user_activity_stream = get_action(u'user_activity_list_html')(
            context, {u'id': g.user_dict[u'id']})

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


user.add_url_rule(u'/reset', view_func=HDXRequestResetView.as_view(str(u'request_reset')))
user.add_url_rule(u'/reset/<id>', view_func=HDXPerformResetView.as_view(str(u'perform_reset')))

_edit_view = HDXEditView.as_view(str(u'edit'))
user.add_url_rule(u'/edit', view_func=_edit_view)
user.add_url_rule(u'/edit/<id>', view_func=_edit_view)

user.add_url_rule(u'/follow_details', view_func=user_onboarding_view.follow_details, methods=(u'POST',))
user.add_url_rule(u'/request_membership', view_func=user_onboarding_view.request_membership, methods=(u'POST',))
user.add_url_rule(u'/request_new_organization', view_func=user_onboarding_view.request_new_organization,
                  methods=(u'POST',))
user.add_url_rule(u'/invite_friends', view_func=user_onboarding_view.invite_friends, methods=(u'POST',))

user.add_url_rule(u'/logged_out_redirect', view_func=hdx_auth_view.logged_out_page)
user.add_url_rule(u'/logged_out_page', view_func=hdx_auth_view.logged_out_page)
user.add_url_rule(u'/logged_in', view_func=hdx_auth_view.logged_in, methods=(u'GET', u'POST',))
user.add_url_rule(u'/login', view_func=_login)
user.add_url_rule(u'/_logout', view_func=_logout)
user.add_url_rule(u'/logged_out', view_func=_logged_out)

user.add_url_rule(u'/follow/<id>', view_func=_follow, methods=(u'POST',))
user.add_url_rule(u'/unfollow/<id>', view_func=_unfollow, methods=(u'POST',))
user.add_url_rule(u'/followers/<id>', view_func=_followers)

user.add_url_rule(u'/generate_key', view_func=_generate_apikey, methods=(u'POST',))

user.add_url_rule(u'/<id>', view_func=read)

hdx_login_link.add_url_rule(u'/login', view_func=hdx_auth_view.new_login)
