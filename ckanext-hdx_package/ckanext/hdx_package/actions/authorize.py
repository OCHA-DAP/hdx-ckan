import ckan.plugins as plugins
import ckan.logic.auth.create as create
import ckan.logic.auth.update as update
from ckan.lib.base import _

import logging

log = logging.getLogger(__name__)

def package_create(context, data_dict=None):
    retvalue = True
    if data_dict and 'groups' in data_dict:
        temp_groups = data_dict['groups']
        del data_dict['groups']
        #check original package_create auth 
        log.info('Removed groups from data_dict: ' + str(data_dict))
        retvalue = create.package_create(context, data_dict)
        data_dict['groups'] = temp_groups
    else:
        retvalue = create.package_create(context, data_dict)

    return retvalue


def package_update(context, data_dict=None):
    retvalue = True
    if data_dict and 'groups' in data_dict:
        temp_groups = data_dict['groups']
        del data_dict['groups']
        #check original package_create auth 
        log.info('Removed groups from data_dict: ' + str(data_dict))
        retvalue = update.package_update(context, data_dict)
        data_dict['groups'] = temp_groups
    else:
        retvalue = update.package_update(context, data_dict)

    return retvalue


def hdx_resource_id_list(context, data_dict=None):
    '''
    Only sysadmins are allowed to call this action
    '''
    return {'success': False, 'msg': _('Only sysadmins can get the entire list of resource ids')}