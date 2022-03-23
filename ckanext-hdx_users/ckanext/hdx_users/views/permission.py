import logging

from flask import Blueprint

import ckan.authz as new_authz
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.permissions as ph
from ckan.views.home import CACHE_PARAMETERS
from ckanext.hdx_users.helpers.permissions import Permissions

log = logging.getLogger(__name__)

# shortcuts
h = tk.h
get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError
clean_dict = logic.clean_dict
tuplize_dict = logic.tuplize_dict
parse_params = logic.parse_params
redirect = h.redirect_to
check_access = tk.check_access
abort = tk.abort
render = tk.render
g = tk.g
_ = tk._
request = tk.request

hdx_user_permission = Blueprint(u'hdx_user_permission', __name__, url_prefix=u'/user/permission')


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


def read(id):
    context = {u'model': model, u'session': model.Session,
               u'user': g.user, u'auth_user_obj': g.userobj,
               u'for_view': True, u'with_related': True}
    try:
        check_access(u'manage_permissions', context, {})
    except Exception as ex:
        abort(404, u'page not found')

    if request.method == 'POST':
        data = clean_dict(
            dict_fns.unflatten(tuplize_dict(parse_params(request.form, ignore_keys=CACHE_PARAMETERS))))
        if data.get(u'update_permissions', u'') == u'update':
            permissions = Permissions(id)
            perm_list = [p for p in Permissions.ALL_PERMISSIONS if p in data]
            permissions.set_permissions({u'user': g.userobj.id}, perm_list)
            redirect(
                h.url_for(u'hdx_user_permission.read', id=id))

    perm_obj = Permissions(id)
    crt_perm = perm_obj.get_permission_list()
    perm_list = []
    for key, value in ph.Permissions.ALL_PERMISSIONS_LABELS_DICT.items():
        _p = {
            u'key': key,
            u'label': value,
            u'checked': True if key in crt_perm else False
        }
        perm_list.append(_p)
    data_dict = {u'id': id,
                 u'user_obj': g.userobj,
                 u'include_datasets': True,
                 u'include_num_followers': True}
    extra_vars = _extra_template_variables(context, data_dict)
    extra_vars[u'permissions'] = perm_list

    return render('user/permission.html', extra_vars=extra_vars)


hdx_user_permission.add_url_rule(u'<id>', methods=[u'GET', u'POST'], view_func=read)
