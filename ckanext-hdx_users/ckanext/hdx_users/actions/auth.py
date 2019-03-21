import ckan.authz as new_authz


## ORGS
def hdx_send_new_org_request(context, data_dict):
    logged_in = new_authz.auth_is_loggedin_user()
    if logged_in:
        return {'success': True}
    else:
        return {'success': False, 'msg': _("You must be logged in to send a new organization request.")}
