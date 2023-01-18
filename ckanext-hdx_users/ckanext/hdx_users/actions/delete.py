import json

import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.helpers.helpers as theme_h

_get_or_bust = tk.get_or_bust
ValidationError = tk.ValidationError
_check_access = tk.check_access
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
get_action = tk.get_action
chained_action = tk.chained_action
OnbUserNotFound = json.dumps({'success': False, 'error': {'message': 'User not found'}})
OnbSuccess = json.dumps({'success': True})


@chained_action
def hdx_user_delete(original_action, context, data_dict):
    '''Delete a user. If user is maintainer for a datasets, it returns error
    copied&adapted from ckan/logic/action/delete.py:L36

    Only sysadmins can delete users.

    :param id: the id or username of the user to delete
    :type id: string
    '''

    _check_access('user_delete', context, data_dict)

    model = context['model']
    user_username = _get_or_bust(data_dict, 'id')
    user_obj = model.User.get(user_username)
    if user_obj:
        user_id = user_obj.id
        if user_id:
            org_list = get_action('organization_list_for_user')(context, {'id': user_id})
            if org_list:
                for org in org_list:
                    pkg_list_for_maintainer = theme_h._get_packages_for_maintainer(context, user_id, org.get('name'))
                    if pkg_list_for_maintainer and len(pkg_list_for_maintainer) > 0:
                        raise NotAuthorized('User can not be deleted as it is maintainer for datasets')

    return original_action(context, data_dict)
