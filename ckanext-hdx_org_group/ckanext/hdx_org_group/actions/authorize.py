from ckan.lib.base import _

import logging

log = logging.getLogger(__name__)


def hdx_trigger_screencap(context, data_dict=None):
    '''
    Only sysadmins are allowed to call this action
    '''
    return {'success': False, 'msg': _('Only sysadmins can get the entire list of resource ids')}
