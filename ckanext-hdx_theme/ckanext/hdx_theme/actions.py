import logging
import datetime

from pylons import config
import sqlalchemy

import ckan.lib.dictization
import ckan.logic as logic
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.model.misc as misc
import ckan.plugins as plugins
import ckan.lib.plugins as lib_plugins
import ckan.new_authz as new_authz
import beaker.cache as bcache

import ckanext.hdx_theme.caching as caching

from ckan.common import _

_check_access = logic.check_access

def organization_list_for_user(context, data_dict):
    '''Return the list of organizations that the user is a member of.

    :param permission: the permission the user has against the returned organizations
      (optional, default: ``edit_group``)
    :type permission: string

    :returns: list of dictized organizations that the user is authorized to edit
    :rtype: list of dicts

    '''
    model = context['model']
    user = context['user']

    _check_access('organization_list_for_user',context, data_dict)
    sysadmin = new_authz.is_sysadmin(user)

    orgs_q = model.Session.query(model.Group) \
        .filter(model.Group.is_organization == True) \
        .filter(model.Group.state == 'active')

    if not sysadmin:
        # for non-Sysadmins check they have the required permission

        permission = data_dict.get('permission', 'edit_group')

        roles = ckan.new_authz.get_roles_with_permission(permission)

        if not roles:
            return []
        user_id = new_authz.get_user_id_for_username(user, allow_none=True)
        if not user_id:
            return []

        q = model.Session.query(model.Member) \
            .filter(model.Member.table_name == 'user') \
            .filter(model.Member.capacity.in_(roles)) \
            .filter(model.Member.table_id == user_id)

        group_ids = []
        for row in q.all():
            group_ids.append(row.group_id)

        if not group_ids:
            return []

        orgs_q = orgs_q.filter(model.Group.id.in_(group_ids))

    orgs_list_complete = orgs_q.all()
    orgs_list = model_dictize.group_list_dictize(orgs_list_complete, context)
    
#to be used in case we want to display the created field
#    org_list_map ={}
#    for it in orgs_list_complete:
#        org_list_map[it.id]=it
#    for it in orgs_list:
#        id=it['id']
#        org = org_list_map[id]
#        it['created']=org.created.isoformat()
    return orgs_list

def cached_group_list(context, data_dict):
    groups  = caching.cached_group_list()
    return groups
    