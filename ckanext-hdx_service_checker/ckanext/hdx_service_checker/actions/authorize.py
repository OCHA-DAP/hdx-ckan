import pylons.config as config

import ckan.plugins as p
from ckan.lib.base import _
from ckan.common import request

@p.toolkit.auth_allow_anonymous_access
def run_checks(context, data_dict=None):
    '''
    Only sysadmins are allowed to call this action
    '''
    if request.user_agent == config.get('hdx.checks.allowed_user_agent', 'HDX-CHECKER'):
        return {'success': True}
    return {'success': False, 'msg': _('Only sysadmins can run checks')}