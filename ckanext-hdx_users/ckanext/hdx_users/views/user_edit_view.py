# encoding: utf-8
import logging

from flask import Blueprint
import ckan.logic as logic
import ckan.lib.authenticator as authenticator
import ckanext.hdx_users.model as user_model
from ckan.views.user import EditView as EditView
from ckan.views.user import set_repoze_user as set_repoze_user
from ckanext.hdx_users.views.user_view_helper import *
import ckan.plugins.toolkit as tk

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
                data = get_action(u'user_show')(context, data_dict)
                # if data.get('firstname') is None or data.get('lastname') is None
                # names_dict = get_action(u'hdx_user_fullname_show')(context, {'user_id': data.get('id')})
                # data['firstname'] = names_dict.get('firstname')
                # data['lastname'] = names_dict.get('lastname')
            except NotAuthorized:
                abort(403, _(u'Unauthorized to edit user %s') % u'')
            except NotFound:
                abort(404, _(u'User not found'))
        return super(HDXEditView, self).get(id, data, errors, error_summary)
