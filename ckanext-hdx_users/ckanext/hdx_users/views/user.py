# encoding: utf-8
import logging
from flask import Blueprint
import json
import ckan.lib.authenticator as authenticator
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.model as user_model
import ckanext.hdx_users.controllers.mailer as hdx_mailer
import ckanext.hdx_users.helpers.tokens as tokens
from ckan.common import _, request, config
from ckan.views.user import EditView as EditView, RequestResetView
from ckan.views.user import PerformResetView
from ckan.views.user import set_repoze_user as set_repoze_user
import ckanext.hdx_users.helpers.helpers as usr_h

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

user = Blueprint(u'hdx_user', __name__, url_prefix=u'/user')

OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbErr = json.dumps({'success': False, 'error': {'message': _('Something went wrong. Please contact support.')}})
OnbSuccess = json.dumps({'success': True})
OnbResetLinkErr = json.dumps({'success': False, 'error': {'message': _('Could not send reset link.')}})

class HDXEditView(EditView):

    def _prepare(self, id):
        context, id = super(HDXEditView, self)._prepare(id)
        context['schema']['email'] = [tk.get_validator('not_empty'), tk.get_validator('user_email_validator'), tk.get_validator('unicode_safe')]
        return context, id

    def post(self, id=None):
        context, id = self._prepare(id)

        if not context[u'save']:
            return self.get(id)

        if id in (g.userobj.id, g.userobj.name):
            current_user = True
        else:
            current_user = False
        old_username = g.userobj.name

        try:
            data_dict = logic.clean_dict(
                dictization_functions.unflatten(
                    logic.tuplize_dict(logic.parse_params(request.form))))
        except dictization_functions.DataError:
            base.abort(400, _(u'Integrity Error'))
        data_dict.setdefault(u'activity_streams_email_notifications', False)

        context[u'message'] = data_dict.get(u'log_message', u'')
        data_dict[u'id'] = id
        email_changed = data_dict[u'email'] != g.userobj.email

        if (data_dict[u'password1']
            and data_dict[u'password2']) or email_changed:
            identity = {
                u'login': g.user,
                u'password': data_dict[u'old_password']
            }
            auth = authenticator.UsernamePasswordAuthenticator()

            if auth.authenticate(request.environ, identity) != g.user:
                errors = {
                    u'oldpassword': [_(u'Password entered was incorrect')]
                }
                error_summary = {_(u'Old Password'): _(u'incorrect password')}
                return self.get(id, data_dict, errors, error_summary)

        try:
            data_dict['fullname'] = data_dict.get('firstname', "") + u' ' + data_dict.get('lastname', "")
            user = logic.get_action(u'user_update')(context, data_dict)
            if user:
                ue_data_dict = {'user_id': user.get('id'), 'extras': [
                    {'key': user_model.HDX_FIRST_NAME, 'new_value': data_dict.get('firstname', '')},
                    {'key': user_model.HDX_LAST_NAME, 'new_value': data_dict.get('lastname', '')},
                ]}
                logic.get_action('user_extra_update')(context, ue_data_dict)
        except logic.NotAuthorized:
            base.abort(403, _(u'Unauthorized to edit user %s') % id)
        except logic.NotFound as ex:
            base.abort(404, _(u'User not found'))
        except logic.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)
        except Exception as ex:
            log.error(ex)

        h.flash_success(_(u'Profile updated'))
        resp = h.redirect_to(u'user.read', id=user[u'name'])
        if current_user and data_dict[u'name'] != old_username:
            # Changing currently logged in user's name.
            # Update repoze.who cookie to match
            set_repoze_user(data_dict[u'name'], resp)
        return resp

    def get(self, id=None, data=None, errors=None, error_summary=None):
        if data is None:
            context, id = self._prepare(id)
            data_dict = {u'id': id}
            try:
                data = logic.get_action(u'user_show')(context, data_dict)
                # if data.get('firstname') is None or data.get('lastname') is None
                # names_dict = logic.get_action(u'hdx_user_fullname_show')(context, {'user_id': data.get('id')})
                # data['firstname'] = names_dict.get('firstname')
                # data['lastname'] = names_dict.get('lastname')
            except logic.NotAuthorized:
                base.abort(403, _(u'Unauthorized to edit user %s') % u'')
            except logic.NotFound:
                base.abort(404, _(u'User not found'))
        return super(HDXEditView, self).get(id, data, errors, error_summary)

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

# HDXRegisterView(MethodView):

user.add_url_rule(u'/reset', view_func=HDXRequestResetView.as_view(str(u'request_reset')))
user.add_url_rule(u'/reset/<id>', view_func=HDXPerformResetView.as_view(str(u'perform_reset')))

_edit_view = HDXEditView.as_view(str(u'edit'))
user.add_url_rule(u'/edit', view_func=_edit_view)
user.add_url_rule(u'/edit/<id>', view_func=_edit_view)

