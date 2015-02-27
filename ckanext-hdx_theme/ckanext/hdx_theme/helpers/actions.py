import json
import logging
# import datetime
import os
import requests


from pylons import config
import sqlalchemy

import ckan.lib.dictization
import ckan.logic as logic
import ckan.plugins.toolkit as tk
import ckan.lib.dictization.model_dictize as model_dictize
# import ckan.model.misc as misc
# import ckan.plugins as plugins
# import ckan.lib.plugins as lib_plugins
import ckan.new_authz as new_authz
import beaker.cache as bcache
import ckan.model as model

import ckanext.hdx_package.helpers.caching as caching
import ckanext.hdx_theme.helpers.counting_actions as counting
import ckanext.hdx_theme.util.mail as hdx_mail
import urllib
import json


from ckan.common import c, _

_check_access = tk.check_access
_get_or_bust = tk.get_or_bust


log = logging.getLogger(__name__)

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
            .filter(model.Member.table_id == user_id) \
            .filter(model.Member.state == 'active')

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
    show_user_info = data_dict.get('user_info', False)
    q_term = data_dict.get('q', None)

    # User must be able to update the group to remove a member from it
    _check_access('group_show', context, data_dict)
    
    q = model.Session.query(model.Member, model.User).\
        filter(model.Member.table_id==model.User.id).\
        filter(model.Member.group_id == group.id).\
        filter(model.Member.state == "active")
    
    if q_term and q_term != '':
        q = q.filter(sqlalchemy.or_(
                     model.User.fullname.ilike('%' + q_term + '%'),
                     model.User.name.ilike('%' + q_term + '%')
                     )
        )

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
    if show_user_info:
        return [(m.table_id, m.table_name, translated_capacity(m.capacity), m.capacity, u.fullname if u.fullname else u.name)
            for m,u in q.all()]
    else:
        return [(m.table_id, m.table_name, translated_capacity(m.capacity), m.capacity)
            for m,u in q.all()]

def cached_group_list(context, data_dict):
    #to make things simpler for caching there's no argument passed
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
            'email': user_obj.email,
            'id': user_obj.id}
    result.update(kw)
    return result

def hdx_get_sys_admins(context, data_dict):
    #TODO: check access that user is logged in
    q = model.Session.query(model.User).filter(model.User.sysadmin==True)
    return [{'name':m.name, 'display_name':m.fullname or m.name, 'email':m.email} for m in q.all()]
    #return q.all();


def hdx_send_new_org_request(context, data_dict):
    _check_access('hdx_send_new_org_request',context, data_dict)

    email = config.get('hdx.orgrequest.email', None)
    if not email:
        email = 'hdx.feedback@gmail.com'
    display_name = 'HDX Feedback'

    ckan_username = c.user
    ckan_email = ''
    if c.userobj:
        ckan_email = c.userobj.email

    subject = _('New organization request:') + ' ' \
        + data_dict['title']
    body = _('New organization request \n' \
        'Organization Name: {org_name}\n' \
        'Organization Description: {org_description}\n' \
        'Organization URL: {org_url}\n' \
        'Person requesting: {person_name}\n' \
        'Person\'s email: {person_email}\n' \
        'Person\'s ckan username: {ckan_username}\n' \
        'Person\'s ckan email: {ckan_email}\n' \
        '(This is an automated mail)' \
    '').format(org_name=data_dict['title'], org_description = data_dict['description'],
               org_url = data_dict['org_url'], person_name = data_dict['your_name'], person_email = data_dict['your_email'],
               ckan_username=ckan_username, ckan_email= ckan_email)

    hdx_mail.send_mail([{'display_name': display_name, 'email': email}], subject, body)


def hdx_send_editor_request_for_org(context, data_dict):
    _check_access('hdx_send_editor_request_for_org',context, data_dict)

    body = _('New request editor/admin role\n' \
    'Full Name: {fn}\n' \
    'Username: {username}\n' \
    'Email: {mail}\n' \
    'Organization: {org}\n' \
    'Message from user: {msg}\n' \
    '(This is an automated mail)' \
    '').format(fn=data_dict['display_name'], username=data_dict['name'], mail=data_dict['email'], 
               org=data_dict['organization'], msg=data_dict.get('message', ''))

    hdx_mail.send_mail(data_dict['admins'], _('New Request Membership'), body)


def hdx_send_request_membership(context, data_dict):
    _check_access('hdx_send_request_membership',context, data_dict)

    body = _('New request membership\n' \
    'Full Name: {fn}\n' \
    'Username: {username}\n' \
    'Email: {mail}\n' \
    'Organization: {org}\n' \
    'Message from user: {msg}\n' \
    '(This is an automated mail)' \
    '').format(fn=data_dict['display_name'], username=data_dict['name'],
               mail=data_dict['email'], org=data_dict['organization'],
               msg=data_dict.get('message', ''))

    hdx_mail.send_mail(data_dict['admins'], _('New Request Membership'), body)

def hdx_user_show(context, data_dict):
    '''Return a user account.

    Either the ``id`` or the ``user_obj`` parameter must be given.

    :param id: the id or name of the user (optional)
    :type id: string
    :param user_obj: the user dictionary of the user (optional)
    :type user_obj: user dictionary

    :rtype: dictionary

    '''
    model = context['model']

    id = data_dict.get('id',None)
    provided_user = data_dict.get('user_obj',None)
    if id:
        user_obj = model.User.get(id)
        context['user_obj'] = user_obj
        if user_obj is None:
            raise NotFound
    elif provided_user:
        context['user_obj'] = user_obj = provided_user
    else:
        raise NotFound

    _check_access('user_show',context, data_dict)

    user_dict = model_dictize.user_dictize(user_obj,context)

    if context.get('return_minimal'):
        return user_dict

    revisions_q = model.Session.query(model.Revision
            ).filter_by(author=user_obj.name)

    revisions_list = []
    for revision in revisions_q.limit(20).all():
        revision_dict = tk.get_action('revision_show')(context,{'id':revision.id})
        revision_dict['state'] = revision.state
        revisions_list.append(revision_dict)
    user_dict['activity'] = revisions_list

    offset = data_dict.get('offset',0)
    limit = data_dict.get('limit',20)
    user_dict['datasets'] = []
    dataset_q = model.Session.query(model.Package).join(model.PackageRole
            ).filter_by(user=user_obj, role=model.Role.ADMIN
            ).offset(offset).limit(limit)

    dataset_q_counter = model.Session.query(model.Package).join(model.PackageRole
            ).filter_by(user=user_obj, role=model.Role.ADMIN
            ).count()

    for dataset in dataset_q:
        try:
            dataset_dict = tk.get_action('package_show')(context, {'id': dataset.id})
        except tk.NotAuthorized:
            continue
        user_dict['datasets'].append(dataset_dict)

    user_dict['num_followers'] = tk.get_action('user_follower_count')(
            {'model': model, 'session': model.Session},
            {'id': user_dict['id']})
    user_dict['total_count'] = dataset_q_counter
    return user_dict

@logic.side_effect_free
def hdx_get_indicator_values(context, data_dict):
    '''
    Makes a call to the REST API that provides the indicator values
    Current param supported are: 
    :param it: indicator types
    :type it: list
    :param l: locations
    :type l: list
    :param s: sources
    :type s: list
    :param minTime: the start year
    :type minTime: int
    :param maxTime: the end year
    :type maxTime: int
    :param periodType: filter the period by another criteria
    :type periodType: string
    :param pageNum: for pagination - page number
    :type pageNum: int
    :param pageSize: for pagination - max number of items in result
    :type pageSize: int
    :param lang: language
    :type lang: string
    '''
    endpoint = config.get('hdx.rest.indicator.endpoint') + '?'

    filter_list = []

    for param_name in ['it', 'l', 'ds', 's', 'minTime', 'maxTime', 'periodType',
                       'pageNum', 'pageSize', 'lang', 'sorting']:
        param_values = data_dict.get(param_name, None)
        filter_list = _add_to_filter_list(param_values, param_name, filter_list)

    filter_list.sort()
    url = endpoint + "&".join(filter_list)

    return _make_rest_api_request(url)

@logic.side_effect_free
def hdx_get_indicator_available_periods(context, data_dict):
    '''
    Makes a call to the REST API that provides the indicator values
    Current param supported are: 
    :param it: indicator types
    :type it: list
    :param l: locations
    :type l: list
    :param s: sources
    :type s: list
    :param minTime: the start year
    :type minTime: int
    :param maxTime: the end year
    :type maxTime: int
    '''
    
    
    endpoint = config.get('hdx.rest.indicator.endpoint.facets') + "/available-periods" + '?'

    filter_list = []

    for param_name in ['it', 'l', 'ds', 's', 'minTime', 'maxTime']:
        param_values = data_dict.get(param_name, None)
        filter_list = _add_to_filter_list(param_values, param_name, filter_list)

    filter_list.sort()
    url = endpoint + "&".join(filter_list)

    return _make_rest_api_request(url)


@bcache.cache_region('hdx_memory_cache', 'cached_make_rest_api_request')
def _make_rest_api_request(url):
    log.info("Requesting indicators:" + url)

    response = requests.get(url)
    return response.json()


def _add_to_filter_list(src, param_name, filter_list):
    if src:
        if isinstance(src, list):
            temp_filters = [
                '{}={}'.format(param_name, elem) for elem in src]
            filter_list = filter_list + temp_filters
        else:
            filter_list.append('{}={}'.format(param_name, src))
            
    return filter_list

def hdx_get_shape_geojson(context, data_dict):
    json_content = None
    try:
        shape_source_url = data_dict.get('shape_source_url', None)
        if shape_source_url is None:
            return None
        shape_src_response = requests.get(shape_source_url, allow_redirects=True)
        urllib.URLopener().retrieve(shape_src_response.url, '/tmp/hdx_shape_temp_file.zip')
        convert_url = data_dict.get('convert_url', u'http://ogre.adc4gis.com/convert')
        shape_data = {'upload': open('/tmp/hdx_shape_temp_file.zip', 'rb')}
        print('Calling Ogre to perform shapefile to geoJSON conversion...')
        try:
            json_resp = requests.post(convert_url, files=shape_data)
        except:
            print("There was an error with the HTTP request")
            raise
        json_content = json.loads(json_resp.content)
        os.remove('/tmp/hdx_shape_temp_file.zip')
        if 'errors' in json_content and json_content['errors']:
            return None
    except :
        print "Error retrieving the json content"
    return json_content
