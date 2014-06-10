import logging
import datetime

from pylons import config
import sqlalchemy

import ckan.lib.dictization
import ckan.plugins.toolkit as tk
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.model.misc as misc
import ckan.plugins as plugins
import ckan.lib.plugins as lib_plugins
import ckan.new_authz as new_authz
import beaker.cache as bcache
import ckan.model as model

import ckanext.hdx_theme.caching as caching
import ckanext.hdx_theme.counting_actions as counting

from ckan.common import _

_check_access = tk.check_access
_get_or_bust = tk.get_or_bust

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

def member_list(context, data_dict=None):
    '''Return the members of a group.

    Modified copy of the original ckan member_list action to also return 
    the non-translated capacity (role)

    :rtype: list of (id, type, translated capacity, capacity ) tuples

    '''
    model = context['model']

    group = model.Group.get(_get_or_bust(data_dict, 'id'))
    if not group:
        raise NotFound

    obj_type = data_dict.get('object_type', None)
    capacity = data_dict.get('capacity', None)

    # User must be able to update the group to remove a member from it
    _check_access('group_show', context, data_dict)

    q = model.Session.query(model.Member).\
        filter(model.Member.group_id == group.id).\
        filter(model.Member.state == "active")

    if obj_type:
        q = q.filter(model.Member.table_name == obj_type)
    if capacity:
        q = q.filter(model.Member.capacity == capacity)

    trans = new_authz.roles_trans()

    def translated_capacity(capacity):
        try:
            return trans[capacity]
        except KeyError:
            return capacity

    return [(m.table_id, m.table_name, translated_capacity(m.capacity), m.capacity)
            for m in q.all()]

def cached_group_list(context, data_dict):
    groups  = caching.cached_group_list()
    return groups

def hdx_basic_user_info(context, data_dict):
    result = {}
    
    _check_access('hdx_basic_user_info', context, data_dict)
    
    model = context['model']
    id = data_dict.get('id',None)
    if id:
        user_obj = model.User.get(id)
        if user_obj is None:
            raise NotFound
        else:
            ds_num  = counting.count_user_datasets(id)
            org_num = counting.count_user_orgs(id)
            grp_num = counting.count_user_grps(id)
            result = _create_user_dict(user_obj, ds_num=ds_num, org_num=org_num, grp_num=grp_num )
    
    return result
            
def _create_user_dict(user_obj, **kw):
    result = { 'display_name': user_obj.fullname or user_obj.name,
            'created': user_obj.created,
            'name': user_obj.name,
            'email': user_obj.email}
    result.update(kw)
    return result

def hdx_get_sys_admins(context, data_dict):
    q = model.Session.query(model.User).filter(model.User.sysadmin==True)
    return [{'name':m.name, 'display_name':m.fullname or m.name, 'email':m.email} for m in q.all()]
    #return q.all();
    
    
    
    
    
    