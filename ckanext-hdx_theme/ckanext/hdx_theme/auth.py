import ckan.new_authz as new_authz
import ckan.logic as logic
import ckan.logic.auth.create as create

from ckan.lib.base import _
from ckan.common import c
import ckan.plugins.toolkit as tk


def _simple_logged_in_auth(fail_message):
    logged_in = new_authz.auth_is_loggedin_user()
    if logged_in:
        return {'success': True}
    else:
        return {'success': False,
                'msg': fail_message}

@logic.auth_sysadmins_check
def group_member_create(context, data_dict):
    try:
        group_dict = tk.get_action('organization_show')(context, {'id': data_dict['id']})
        # if the above call returns we already know it is an organization
        # otherwise a NotFound is raised
        return create.group_member_create(context, data_dict)
    except logic.NotFound:
        # means the specific group is surely not an org or doesn't exist at all
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
