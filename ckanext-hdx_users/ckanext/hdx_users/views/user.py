# encoding: utf-8
import logging
from flask import Blueprint

import ckan.lib.authenticator as authenticator
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.model as user_model
from ckan.common import _, request
from ckan.common import g
from ckan.views.user import EditView as EditView
from ckan.views.user import PerformResetView
from ckan.views.user import set_repoze_user as set_repoze_user

log = logging.getLogger(__name__)

render = tk.render
abort = tk.abort
get_action = tk.get_action
check_access = tk.check_access
request = tk.request
h = tk.h
_ = tk._

redirect = tk.redirect_to

NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound

user = Blueprint(u'hdx_user', __name__, url_prefix=u'/user')


class HDXEditView(EditView):
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
            data_dict['fullname'] = data_dict.get('firstname') + u' ' + data_dict.get('lastname')
            user = logic.get_action(u'user_update')(context, data_dict)
            if user:
                ue_data_dict = {'user_id': user.get('id'), 'extras': [
                    {'key': user_model.HDX_FIRST_NAME, 'new_value': data_dict.get('firstname', '')},
                    {'key': user_model.HDX_LAST_NAME, 'new_value': data_dict.get('lastname', '')},
                ]}
                logic.get_action('user_extra_update')(context, ue_data_dict)
        except logic.NotAuthorized:
            base.abort(403, _(u'Unauthorized to edit user %s') % id)
        except logic.NotFound, ex:
            base.abort(404, _(u'User not found'))
        except logic.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
            return self.get(id, data_dict, errors, error_summary)

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


class HDXPerformResetView(PerformResetView):

    def get(self, id):
        context = {
            u'model': model,
            u'session': model.Session,
            u'keep_email': True
        }

        g.reset_key = request.params.get(u'key')
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
            return _forgot_password()

        try:
            user_dict = get_action(u'user_show')(context, {u'id': id})
        except NotFound:
            abort(404, _(u'User not found'))

        return render(u'user/perform_reset.html', {
            u'user_dict': user_dict
        })


def _forgot_password():
    return render('user/forgot_password.html')


user.add_url_rule(
    u'/reset', view_func=_forgot_password)

user.add_url_rule(
    u'/reset/<id>', view_func=HDXPerformResetView.as_view(str(u'perform_reset')))

_edit_view = HDXEditView.as_view(str(u'edit'))
user.add_url_rule(u'/edit', view_func=_edit_view)
user.add_url_rule(u'/edit/<id>', view_func=_edit_view)
