import datetime
import logging

import dateutil.parser
import pylons.config as config

import ckan.authz as new_authz
import ckan.logic as logic
import ckan.logic.auth.update as core_auth_update
from ckan.common import _

log = logging.getLogger(__name__)

## ORGS
def hdx_send_new_org_request(context, data_dict):
    logged_in = new_authz.auth_is_loggedin_user()
    if logged_in:
        return {'success': True}
    else:
        return {'success': False, 'msg': _("You must be logged in to send a new organization request.")}


## USERS
def manage_permissions(context, data_dict):
    return {'success': False, 'msg': _('Only sysadmins can view user permission page')}


def hdx_first_login(context, data_dict):
    if context.get('auth_user_obj'):
        return {'success': True}
    else:
        return {'success': False, 'msg': _("You must be logged in to send a first_login update")}


@logic.auth_allow_anonymous_access
def user_update(context, data_dict):
    if data_dict.get('reset_key'):
        key_parts = data_dict.get('reset_key').split('__')
        if len(key_parts) != 2:
            return {'success': False, 'msg': _("Reset key has wrong format")}
        else:
            time_part = key_parts[1]
            try:
                key_time = dateutil.parser.parse(time_part)
                now_time = datetime.datetime.utcnow()
                if now_time > key_time:
                    return {'success': False, 'msg': _("Reset key no longer valid")}
            except Exception as e:
                log.warning(str(e))

    return core_auth_update.user_update(context, data_dict)


