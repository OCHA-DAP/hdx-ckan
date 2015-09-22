import ckan.plugins as plugins
import ckan.logic.auth.create as create
import ckan.logic.auth.update as update
from ckan.lib.base import _

import logging

log = logging.getLogger(__name__)

def hdx_generate_thumbnails(context, data_dict=None):
    '''
    Only sysadmins are allowed to call this action
    '''
    return {'success': False, 'msg': _('Only sysadmins can get the entire list of resource ids')}