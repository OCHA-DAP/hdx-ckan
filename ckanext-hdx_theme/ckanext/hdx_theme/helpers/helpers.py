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

import ckanext.hdx_theme.helpers.counting_actions as counting

from webhelpers.html import escape, HTML, literal, url_escape
from ckan.common import _
import urlparse as urlparse
import pylons.config as config

log = logging.getLogger(__name__)

downloadable_formats = {
    'csv', 'xls', 'xlsx', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'xml'
}


def is_downloadable(resource):
    format = resource.get('format', 'data').lower()
    if format in downloadable_formats:
        return True
    return False


def get_facet_items_dict(facet, limit=1000, exclude_active=False):
    facets = h.get_facet_items_dict(
        facet, limit, exclude_active=exclude_active)
    filtered_no_items = c.search_facets.get(facet)['items'].__len__()
    total_no_items = json.loads(
        count.CountController.list[facet](count.CountController()))['count']
    if filtered_no_items < 50 and filtered_no_items < total_no_items:
        no_items = filtered_no_items
    else:
        no_items = total_no_items

    if c.search_facets_limits:
        limit = c.search_facets_limits.get(facet)
    if limit:
        return (facets[:limit], no_items)
    else:
        return (facets, no_items)


def get_last_modifier_user(g_id=None, p_id=None, get_timestamp=False):
    if g_id is not None:
        activity_objects = model.activity.group_activity_list(
            g_id, limit=1, offset=0)
    if p_id is not None:
        activity_objects = model.activity.package_activity_list(
            p_id, limit=1, offset=0)
    if activity_objects:
        user = activity_objects[0].user_id
        t_stamp = activity_objects[0].timestamp
        if get_timestamp:
            return (model.User.get(user), t_stamp.isoformat())
        return model.User.get(user)

    # in case there is no update date it will be displayed the current date
    user = model.Session.query(model.User).filter(
        model.User.name == 'hdx').first()
    if get_timestamp:
        return (user, datetime.datetime.now().isoformat())
    return user


def get_filtered_params_list(params):
    result = []
    for (key, value) in params.items():
        if key not in {'q', 'sort'}:
            result.append((key, value))
    return result


def get_last_revision_package(package_id):
    #     pkg_list  = model.Session.query(model.Package).filter(model.Package.id == package_id).all()
    #     pkg = pkg_list[0]
    #     return pkg.latest_related_revision.id
    activity_objects = model.activity.package_activity_list(
        package_id, limit=1, offset=0)
    if len(activity_objects) > 0:
        activity = activity_objects[0]
        return activity.revision_id
    return None


def get_last_revision_group(group_id):
    #     grp_list  = model.Session.query(model.Group).filter(model.Group.id == group_id).all()
    #     grp = grp_list[0]
    #     last_rev = grp.all_related_revisions[0][0]
    activity_objects = model.activity.group_activity_list(
        group_id, limit=1, offset=0)
    if len(activity_objects) > 0:
        activity = activity_objects[0]
        return activity.revision_id
    return None


def get_last_revision_timestamp_group(group_id):
    activity_objects = model.activity.group_activity_list(
        group_id, limit=1, offset=0)
    if len(activity_objects) > 0:
        activity = activity_objects[0]
        return h.render_datetime(activity.timestamp)
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
        user = tk.get_action('hdx_basic_user_info')(context, {'id': user_id})
    except logic.NotAuthorized:
        base.abort(401, _('Unauthorized to see organization member list'))
    return user


def markdown_extract_strip(text, extract_length=190):
    ''' return the plain text representation of markdown encoded text.  That
    is the texted without any html tags.  If extract_length is 0 then it
    will not be truncated.'''
    result_text = h.markdown_extract(text, extract_length)
    result = result_text.rstrip('\n').replace(
        '\n', ' ').replace('\r', '').replace('"', "&quot;")
    return result

def render_markdown_strip(text, extract_length=190):
    ''' return the plain text representation of markdown encoded text.  That
    is the texted without any html tags.  If extract_length is 0 then it
    will not be truncated.'''
    result_text = h.render_markdown(text, extract_length)
    result = result_text.rstrip('\n').replace(
        '\n', ' ').replace('\r', '').replace('"', "&quot;")
    return result

def methodology_bk_compat(meth, other, render=True):
    if not meth and not other:
        return (None, None)
    standard_meths = ["Census","Sample Survey","Direct Observational Data/Anecdotal Data","Registry","Other"]
    if meth in standard_meths and meth != "Other":
        if render:
            return (h.render_markdown(meth), None)
        else:
            return (h.markdown_extract(meth), None)
    elif other:
        if render:
            return ("Other", h.render_markdown(other))
        else:
            return ("Other", h.markdown_extract(other))
    else:
        meth =  meth.split('Other - ')
        if render:
            return ("Other", h.render_markdown(meth[0]))
        else:
            return ("Other", h.markdown_extract(meth[0]))


def render_date_from_concat_str(str, separator='-'):
    result = ''
    if str:
        strdate_list = str.split(separator)
        for index, strdate in enumerate(strdate_list):
            try:
                date = datetime.datetime.strptime(strdate.strip(), '%m/%d/%Y')
                render_strdate = date.strftime('%b %d, %Y')
                result += render_strdate
                if index < len(strdate_list) - 1:
                    result += ' - '
            except ValueError, e:
                log.warning(e)

    return result


def hdx_build_nav_icon_with_message(menu_item, title, **kw):
    htmlResult = h.build_nav_icon(menu_item, title, **kw)
    if 'message' not in kw or not kw['message']:
        return htmlResult
    else:
        newResult = str(htmlResult).replace('</a>',
                                            ' <span class="nav-short-message">{message}</span></a>'.format(message=kw['message']))
        return h.literal(newResult)


def hdx_linked_user(user, maxlength=0):
    response = h.linked_user(user, maxlength)
    changed_response = re.sub(r"<img[^>]+/>", "", response)
    return h.literal(changed_response)


def hdx_show_singular_plural(num, singular_word, plural_word, show_number=True):
    response = None
    if num == 1:
        response = singular_word
    else:
        response = plural_word

    if show_number:
        return str(num) + ' ' + response
    else:
        return response


def hdx_num_of_new_related_items():
    max_days = 30
    count = 0
    now = datetime.datetime.now()
    for related in c.pkg.related:
        if (related.created):
            difference = now - related.created
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


def hdx_get_extras_element(extras, key='key', value_key='org_url', ret_key='value'):
    res = ''
    for ex in extras:
        if ex[key] == value_key:
            res = ex[ret_key]
    return res


def hdx_group_followee_list():

    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'auth_user_obj': c.userobj,
               'for_view': True}

    list = logic.get_action('group_followee_list')(
        context, {'id': c.userobj.id})
    # filter out the orgs
    groups = [group for group in list if not group['is_organization']]

    return groups


def hdx_organizations_available_with_roles():
    organizations_available = h.organizations_available('read')
    if organizations_available and len(organizations_available) > 0:
        orgs_where_editor = []
        orgs_where_admin = []
    am_sysadmin = new_authz.is_sysadmin(c.user)
    if not am_sysadmin:
        orgs_where_editor = set(
            [org['id'] for org in h.organizations_available('create_dataset')])
        orgs_where_admin = set([org['id']
                                for org in h.organizations_available('admin')])

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


def hdx_remove_schema_and_domain_from_url(url):
    urlTuple = urlparse.urlparse(url)
    if url.endswith('/preview'):
        # this is the case when the file needs to be transformed
        # before it can be previewed

        modifiedTuple = (('', '') + urlTuple[2:6])
    else:
        # this is for txt files
        # we force https since otherwise the browser will
        # anyway block loading mixed active content
        modifiedTuple = (('',) + urlTuple[1:6])
    modifiedUrl = urlparse.urlunparse(modifiedTuple)
    return modifiedUrl


def hdx_get_ckan_config(config_name):
    return config.get(config_name)


def get_group_name_from_list(glist, gid):
    for group in glist:
        if group['id'] == gid:
            return group['title']
    return ""


def hdx_follow_link(obj_type, obj_id, extra_text, cls=None):
    obj_type = obj_type.lower()
    assert obj_type in h._follow_objects
    # If the user is logged in show the follow/unfollow button
    if c.user:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        action = 'am_following_%s' % obj_type
        following = logic.get_action(action)(context, {'id': obj_id})
        return h.snippet('search/snippets/follow_link.html',
                         following=following,
                         obj_id=obj_id,
                         obj_type=obj_type,
                         extra_text=extra_text,
                         cls=cls)
    return ''


def follow_status(obj_type, obj_id):
    obj_type = obj_type.lower()
    assert obj_type in h._follow_objects
    # If the user is logged in show the follow/unfollow button
    if c.user:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        action = 'am_following_%s' % obj_type
        following = logic.get_action(action)(context, {'id': obj_id})
        return following
    return False


def one_active_item(items):
    for i in items:
        if i['active']:
            return True
    return False


def feature_count(features):
    count = 0
    for name in features:
        facet = h.get_facet_items_dict(name)
        for f in facet:
            count += f['count']
    return count


def hdx_follow_button(obj_type, obj_id, **kw):
    ''' This is a modified version of the ckan core follow_button() helper
    It returns a simple link for a bootstrap dropdown menu

    Return a follow button for the given object type and id.

    If the user is not logged in return an empty string instead.

    :param obj_type: the type of the object to be followed when the follow
        button is clicked, e.g. 'user' or 'dataset'
    :type obj_type: string
    :param obj_id: the id of the object to be followed when the follow button
        is clicked
    :type obj_id: string

    :returns: a follow button as an HTML snippet
    :rtype: string

    '''
    obj_type = obj_type.lower()
    assert obj_type in h._follow_objects
    # If the user is logged in show the follow/unfollow button
    if c.user:
        context = {'model': model, 'session': model.Session, 'user': c.user}
        action = 'am_following_%s' % obj_type
        following = logic.get_action(action)(context, {'id': obj_id})
        return h.snippet('snippets/hdx_follow_button.html',
                         following=following,
                         obj_id=obj_id,
                         obj_type=obj_type,
                         params=kw)
    return ''

def hdx_add_url_param(alternative_url=None, controller=None, action=None,
                  extras=None, new_params=None, unwanted_keys = []):
    '''
    MODIFIED CKAN HELPER THAT ALLOWS REMOVING SOME PARAMS
    
    Adds extra parameters to existing ones

    controller action & extras (dict) are used to create the base url
    via url_for(controller=controller, action=action, **extras)
    controller & action default to the current ones

    This can be overriden providing an alternative_url, which will be used
    instead.
    '''

    params_nopage = [(k, v) for k, v in request.params.items() 
                     if k != 'page' and k not in unwanted_keys]
    params = set(params_nopage)
    if new_params:
        params |= set(new_params.items())
    if alternative_url:
        return h._url_with_params(alternative_url, params)
    return h._create_url_with_params(params=params, controller=controller,
                                   action=action, extras=extras)
    
    