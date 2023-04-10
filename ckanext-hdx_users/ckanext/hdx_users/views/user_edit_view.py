# encoding: utf-8
import logging
import json

from flask import Blueprint
import ckan.logic as logic
import ckan.lib.base as base
import ckan.model as model
from ckan.common import asbool, config, session
import ckan.lib.authenticator as authenticator
import ckanext.hdx_users.model as user_model
from ckan.views.user import EditView as EditView
from ckan.views.user import _extra_template_variables
from ckan.views.user import set_repoze_user as set_repoze_user

import ckan.plugins.toolkit as tk
from ckanext.hdx_users.views.user_view_helper import *
from ckanext.security import utils
from ckanext.security.cache.login import LoginThrottle
from ckanext.security.model import SecurityTOTP
from ckan.lib import helpers
log = logging.getLogger(__name__)

render = tk.render
abort = tk.abort
get_action = tk.get_action
check_access = tk.check_access
request = tk.request
h = tk.h
_ = tk._
g = tk.g
User = model.User

redirect = tk.redirect_to

NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError

class HDXTwoStep:
    @staticmethod
    def configure_mfa(id=None):
        tc = utils.configure_mfa(id)
        if helpers.are_there_flash_messages():
            helpers._flash.pop_messages()
        helpers.flash_success("Successfully configured and enabled the two-step verification.")
        session['totp_enabled'] = True
        return json.dumps({'success': (tc.mfa_test_valid == True)})

    @staticmethod
    def new(id=None):
        utils.new(id)
        tc = utils.configure_mfa(id)
        if helpers.are_there_flash_messages():
            helpers._flash.pop_messages()
        helpers.flash_error("Two-step verification enabled. "
                            "Please add the new secret to your authenticator app and verify the code to ensure it is working ok.")
        return json.dumps({
            'success': True,
            'totp_challenger_uri': tc.totp_challenger_uri,
            'totp_secret': tc.totp_secret
        })

    @staticmethod
    def delete(id=None):
        totp_challenger = SecurityTOTP.get_for_user(id)
        if helpers.are_there_flash_messages():
            helpers._flash.pop_messages()
        helpers.flash_success("Successfully disabled the two-step verification.")
        if totp_challenger:
            totp_challenger.delete()
            totp_challenger.commit()
        session['totp_enabled'] = False
        return json.dumps({'success': True})

    @staticmethod
    def check_lockout():
        user_name = SecurityTOTP.get_user_name(request.args['user'])
        locked = False
        lockout = {}
        throttle = LoginThrottle(User.by_name(user_name), user_name)
        if throttle:
            locked = throttle.is_locked()
            if locked:
                lockout['timeout'] = throttle.login_lock_timeout

        lockout['result'] = locked
        return json.dumps(lockout)

    @staticmethod
    def check_mfa():
        user_name = SecurityTOTP.get_user_name(request.args['user'])
        totp_challenger = SecurityTOTP.get_for_user(user_name)
        return json.dumps({'result': totp_challenger is not None})


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
            abort(400, _(u'Integrity Error'))
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

            auth_user_id = auth.authenticate(request.environ, identity)
            if auth_user_id:
                auth_user_id = auth_user_id.split(u',')[0]
            if auth_user_id != g.userobj.id:
                errors = {
                    u'oldpassword': [_(u'Password entered was incorrect')]
                }
                error_summary = {_(u'Old Password'): _(u'incorrect password')} \
                    if not g.userobj.sysadmin \
                    else {_(u'Sysadmin Password'): _(u'incorrect password')}
                return self.get(id, data_dict, errors, error_summary)

        try:
            data_dict['fullname'] = data_dict.get('firstname', "") + u' ' + data_dict.get('lastname', "")
            user = get_action(u'user_update')(context, data_dict)
            if user:
                ue_data_dict = {'user_id': user.get('id'), 'extras': [
                    {'key': user_model.HDX_FIRST_NAME, 'new_value': data_dict.get('firstname', '')},
                    {'key': user_model.HDX_LAST_NAME, 'new_value': data_dict.get('lastname', '')},
                ]}
                get_action('user_extra_update')(context, ue_data_dict)
        except NotAuthorized:
            abort(403, _(u'Unauthorized to edit user %s') % id)
        except NotFound as ex:
            abort(404, _(u'User not found'))
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)
        except Exception as ex:
            log.error(ex)

        h.flash_success(_(u'Profile updated'))
        resp = h.redirect_to(u'hdx_user.edit', id=user[u'name'])
        if current_user and data_dict[u'name'] != old_username:
            # Changing currently logged in user's name.
            # Update repoze.who cookie to match
            set_repoze_user(data_dict[u'name'], resp)
        return resp

    def get(self, id=None, data=None, errors=None, error_summary=None):
        if data is None:
            context, id = self._prepare(id)
            data_dict = {u'id': id, u'include_num_followers': True}
            try:
                data = get_action(u'user_show')(context, data_dict)
            except NotAuthorized:
                abort(403, _(u'Unauthorized to edit user %s') % u'')
            except NotFound:
                abort(404, _(u'User not found'))
        data['user_dict'] = data

        context, id = self._prepare(id)
        data_dict = {u'id': id, u'include_num_followers': True}
        try:
            old_data = logic.get_action(u'user_show')(context, data_dict)

            g.display_name = old_data.get(u'display_name')
            g.user_name = old_data.get(u'name')

            data = data or old_data

        except logic.NotAuthorized:
            base.abort(403, _(u'Unauthorized to edit user %s') % u'')
        except logic.NotFound:
            base.abort(404, _(u'User not found'))
        user_obj = context.get(u'user_obj')

        errors = errors or {}
        vars = {
            u'data': data,
            u'errors': errors,
            u'error_summary': error_summary
        }

        extra_vars = _extra_template_variables({
            u'model': model,
            u'session': model.Session,
            u'user': g.user
        }, data_dict)

        extra_vars[u'show_email_notifications'] = asbool(
            config.get(u'ckan.activity_streams_email_notifications'))
        vars.update(extra_vars)
        tc = utils._setup_totp_template_variables(context, data_dict)
        if hasattr(tc, 'totp_challenger_uri'):
            g.totp_challenger_uri = tc.totp_challenger_uri
        if hasattr(tc, 'totp_secret'):
            g.totp_secret = tc.totp_secret
        return base.render(u'user/edit_user_form.html', extra_vars=vars)
