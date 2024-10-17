import ckan.plugins.toolkit as tk
from ckan.common import request

_ = tk._
config = tk.config


@tk.auth_allow_anonymous_access
def run_checks(context, data_dict=None):
    '''
    Only sysadmins are allowed to call this action
    '''
    if request.user_agent.string == config.get('hdx.checks.allowed_user_agent'):
        return {'success': True}
    return {'success': False, 'msg': _('Only sysadmins can run checks')}
