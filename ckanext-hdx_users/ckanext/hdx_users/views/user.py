# encoding: utf-8
import json
import logging

from flask import Blueprint

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.controllers.mailer as hdx_mailer
import ckanext.hdx_users.helpers.helpers as usr_h
import ckanext.hdx_users.helpers.tokens as tokens
from ckan.common import _, request, config
from ckan.views.user import PerformResetView
from ckan.views.user import RequestResetView
from ckanext.hdx_users.views.user_register_view import HDXRegisterView
from ckanext.hdx_users.views.user_edit_view import HDXEditView

log = logging.getLogger(__name__)

render = tk.render
abort = tk.abort
get_action = tk.get_action
check_access = tk.check_access
request = tk.request
h = tk.h
_ = tk._
g = tk.g

redirect = tk.redirect_to

NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError

hdx_register_view = HDXRegisterView()
user = Blueprint(u'hdx_user', __name__, url_prefix=u'/user')

OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbErr = json.dumps({'success': False, 'error': {'message': _('Something went wrong. Please contact support.')}})
OnbSuccess = json.dumps({'success': True})
OnbResetLinkErr = json.dumps({'success': False, 'error': {'message': _('Could not send reset link.')}})


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
            base.abort(403, _('Unauthorized to request reset password.'))
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

user.add_url_rule(u'/reset', view_func=HDXRequestResetView.as_view(str(u'request_reset')))
user.add_url_rule(u'/reset/<id>', view_func=HDXPerformResetView.as_view(str(u'perform_reset')))

_edit_view = HDXEditView.as_view(str(u'edit'))
user.add_url_rule(u'/edit', view_func=_edit_view)
user.add_url_rule(u'/edit/<id>', view_func=_edit_view)

user.add_url_rule(u'/register_email', view_func=hdx_register_view.register_email, methods=(u'POST', ))
