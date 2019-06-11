import logging

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.lib.helpers as h
from ckan.common import c, request
import ckan.lib.navl.dictization_functions as dict_fns

import ckanext.hdx_users.controllers.dashboard_controller as dashboard_controller
import ckanext.hdx_users.helpers.permissions as ph
from ckan.controllers.home import CACHE_PARAMETERS
from ckanext.hdx_users.helpers.permissions import Permissions

log = logging.getLogger(__name__)

# shortcuts
get_action = logic.get_action
NotAuthorized = logic.NotAuthorized
NotFound = logic.NotFound
ValidationError = logic.ValidationError
clean_dict = logic.clean_dict
tuplize_dict = logic.tuplize_dict
parse_params = logic.parse_params
redirect = h.redirect_to


class PermissionController(dashboard_controller.DashboardController):

    def permission(self, id):

        if request.method == 'POST':
            data = clean_dict(
                dict_fns.unflatten(tuplize_dict(parse_params(request.params, ignore_keys=CACHE_PARAMETERS))))
            if data.get('update_permissions', '') == 'update':
                permissions = Permissions(id)
                perm_list = [p for p in Permissions.ALL_PERMISSIONS if p in data]
                permissions.set_permissions({'user': c.userobj.id}, perm_list)
                redirect(
                    h.url_for(controller='ckanext.hdx_users.controllers.permission_controller:PermissionController',
                              action='permission', id=id))

        context = {'model': model, 'session': model.Session,
                   'user': c.user, 'auth_user_obj': c.userobj,
                   'for_view': True, 'with_related': True}
        data_dict = {'id': id,
                     'user_obj': c.userobj,
                     'include_datasets': True,
                     'include_num_followers': True}
        extra_vars = self._extra_template_variables(context, data_dict)

        perm_obj = Permissions(id)
        crt_perm = perm_obj.get_permission_list()
        perm_list = []
        for key, value in ph.Permissions.ALL_PERMISSIONS_DICT.items():
            _p = {
                'key': key,
                'label': value,
                'checked': True if key in crt_perm else False
            }
            perm_list.append(_p)
        extra_vars['permissions'] = perm_list

        return base.render('user/permission.html', extra_vars=extra_vars)
