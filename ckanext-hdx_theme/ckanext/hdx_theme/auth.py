import ckan.new_authz as new_authz
import ckan.logic as logic

from ckan.lib.base import _


def hdx_basic_user_info(context, data_dict):
    logged_in = new_authz.auth_is_loggedin_user()
    if logged_in:
        return {'success': True}
    else:
        return {'success': False,
                'msg': _("You must be logged in to access basic organization member info.")}


@logic.auth_sysadmins_check
def group_member_create(context, data_dict):
    return {'success': False, 'msg': _('Nobody can add a member to a country in HDX')}