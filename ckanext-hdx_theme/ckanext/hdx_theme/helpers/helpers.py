from ckan.controllers import group
import ckan.lib.helpers as h
from ckan.common import (
     c, request
)
import sqlalchemy
import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic
import datetime
import ckanext.hdx_theme.version as version
import count
import json
import logging
import ckan.plugins.toolkit as tk
import re
import ckan.new_authz as new_authz

import ckanext.hdx_theme.counting_actions as counting

from webhelpers.html import escape, HTML, literal, url_escape
from ckan.common import _

log = logging.getLogger(__name__)

downloadable_formats = {
    'csv', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'xml'
}

def is_downloadable(resource):
    format = resource.get('format', 'data').lower()
    if format in downloadable_formats:
        return True
    return False

def get_facet_items_dict(facet, limit=10, exclude_active=False):
    facets = h.get_facet_items_dict(facet, limit, exclude_active=exclude_active)
    filtered_no_items = c.search_facets.get(facet)['items'].__len__()
    total_no_items=json.loads(count.CountController.list[facet](count.CountController()))['count']
    if filtered_no_items < 50 and filtered_no_items < total_no_items:
        no_items=filtered_no_items
    else:
        no_items=total_no_items

    if c.search_facets_limits:
        limit = c.search_facets_limits.get(facet)
    if limit:
        return (facets[:limit],no_items)
    else:
        return (facets,no_items)
    
def get_last_modifier_user(rev_id, get_timestamp=False):
    act_list = model.Session.query(model.Activity).filter(model.Activity.revision_id == rev_id).all()
    if act_list and len(act_list)>0:
        act = act_list[0]
        usr_id = act.user_id
        if get_timestamp:
            return (model.User.get(usr_id), act.timestamp.isoformat())
        return model.User.get(usr_id)
    #in case there is no update date it will be displayed the current date
    usr_list = model.Session.query(model.User).filter(model.User.name == 'hdx').all()
    usr = usr_list[0]
    return (usr.id, datetime.datetime.now().isoformat())

def get_filtered_params_list(params):
    result = []
    for (key, value) in params.items():
        if key not in {'q','sort'} :
            result.append((key,value))
    return result;

def get_last_revision_package(package_id):
#     pkg_list  = model.Session.query(model.Package).filter(model.Package.id == package_id).all()
#     pkg = pkg_list[0]
#     return pkg.latest_related_revision.id
    activity_objects = model.activity.package_activity_list(package_id, limit=1, offset=0)
    if len(activity_objects)>0 :
        activity = activity_objects[0]
        return activity.revision_id
    return None


def get_last_revision_group(group_id):
#     grp_list  = model.Session.query(model.Group).filter(model.Group.id == group_id).all()
#     grp = grp_list[0]
#     last_rev = grp.all_related_revisions[0][0]
    activity_objects = model.activity.group_activity_list(group_id, limit=1, offset=0)
    if len(activity_objects)>0 :
        activity = activity_objects[0]
        return activity.revision_id
    return None

def get_group_followers(grp_id):
    result = logic.get_action('group_follower_count')(
            {'model': model, 'session': model.Session},
            {'id': grp_id})
    return result

def get_group_members(grp_id):
    member_list = logic.get_action('member_list')(
            {'model': model, 'session': model.Session},
            {'id': grp_id, 'object_type': 'user'})
    result = len(member_list)
    return result

def hdx_get_user_info(user_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}
    try:
        user    = tk.get_action('hdx_basic_user_info')(context,{'id':user_id})
    except logic.NotAuthorized:
            base.abort(401, _('Unauthorized to see organization member list'))    
        
    return user

def markdown_extract_strip(text, extract_length=190):
    ''' return the plain text representation of markdown encoded text.  That
    is the texted without any html tags.  If extract_length is 0 then it
    will not be truncated.'''
    result_text = h.markdown_extract(text, extract_length)
    result = result_text.rstrip('\n').replace('\n', ' ').replace('\r', '')
    return result

def render_date_from_concat_str(str, separator='-'):
    result  = ''
    if str:
        strdate_list    = str.split(separator)
        for index,strdate in enumerate(strdate_list):
            try:
                date = datetime.datetime.strptime(strdate.strip(), '%m/%d/%Y')
                render_strdate  = date.strftime('%b %d, %Y');
                result  += render_strdate
                if index < len(strdate_list)-1:
                    result += ' - '
            except ValueError, e:
                log.warning(e)
    
    return result

def hdx_build_nav_icon_with_message(menu_item, title, **kw):
    htmlResult  = h.build_nav_icon(menu_item, title, **kw)
    if 'message' not in kw or not kw['message']:
        return htmlResult
    else:
        newResult   = str(htmlResult).replace('</a>', 
                    ' <span class="nav-short-message">{message}</span></a>'.format(message=kw['message']) )
        return h.literal(newResult)
    
def hdx_linked_user(user, maxlength=0):
    response = h.linked_user(user, maxlength)
    changed_response = re.sub(r"<img[^>]+/>","",str(response))
    return h.literal(changed_response)

def hdx_show_singular_plural(num, singular_word, plural_word):
    if num == 1:
        return str(num) + ' ' + singular_word
    else:
        return str(num) + ' ' + plural_word

def hdx_num_of_new_related_items():
    max_days = 30;
    count = 0;
    now = datetime.datetime.now()
    for related in c.pkg.related:
        if (related.created):
            difference  = now-related.created
            days = difference.days
            if days < max_days:
                count += 1
    return count

def hdx_member_roles_list():
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}
    return tk.get_action('member_roles_list')(context, {})

def hdx_version():
    return version.hdx_version

def hdx_get_extras_element(extras, key='key', value_key='org_url', ret_key='value' ):
    res = ''
    for ex in extras :
        if ex[key] == value_key:
            res = ex[ret_key]
    return res

def hdx_group_followee_list():

    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj,
               'for_view': True}

    list = logic.get_action('group_followee_list')(context, {'id': c.userobj.id})
    #filter out the orgs
    groups = [group for group in list if not group['is_organization']]

    return groups


def hdx_organizations_available_with_roles():
    organizations_available = h.organizations_available('read')
    if organizations_available and len(organizations_available) > 0:
        orgs_where_editor = []
        orgs_where_admin = []
    am_sysadmin = new_authz.is_sysadmin(c.user)
    if not am_sysadmin:
        orgs_where_editor = set([org['id'] for org in h.organizations_available('create_dataset')])
        orgs_where_admin = set([org['id'] for org in h.organizations_available('admin')])

    for org in organizations_available:
        org['has_add_dataset_rights'] = True
        if am_sysadmin:
            org['role'] = 'sysadmin'
        elif org['id'] in orgs_where_admin:
            org['role'] = 'admin'
        elif org['id'] in orgs_where_editor:
            org['role'] = 'editor'
        else:
            org['role'] = 'member'
            org['has_add_dataset_rights'] = False

    organizations_available.sort(key=lambda y:
                                y['display_name'].lower())
    return organizations_available

