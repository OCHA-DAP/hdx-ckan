import ckan.new_authz as new_authz
import ckan.logic as logic

from ckan.lib.base import _


def _simple_logged_in_auth(fail_message):
    logged_in = new_authz.auth_is_loggedin_user()
    if logged_in:
        return {'success': True}
    else:
        return {'success': False,
                'msg': fail_message}

@logic.auth_sysadmins_check
def group_member_create(context, data_dict):
    return {'success': False, 'msg': _('Nobody can add a member to a country in HDX')}


def hdx_basic_user_info(context, data_dict):
    return _simple_logged_in_auth(_("You must be logged in to access basic \
                            organization member info."))


def hdx_send_new_org_request(context, data_dict):
    return _simple_logged_in_auth(_("You must be logged in to send a new \
                            organization request."))


def hdx_send_editor_request_for_org(context, data_dict):
    return _simple_logged_in_auth(_("You must be logged in to send a request \
                            for being an editor."))


def hdx_send_request_membership(context, data_dict):
    return _simple_logged_in_auth(_("You must be logged in to send a  \
                            membership request."))
