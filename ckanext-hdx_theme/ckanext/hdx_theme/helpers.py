import ckan.lib.helpers as h
from ckan.common import (
     c, request
)
import ckan.model as model
import sqlalchemy
import ckan.logic as logic
import datetime
from webhelpers.html import escape, HTML, literal, url_escape

downloadable_formats = {
    'csv', 'xls', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'xml'
}

def is_downloadable(resource):
    format = resource.get('format', 'data').lower()
    if format in downloadable_formats:
        return True
    return False

def get_facet_items_dict(facet, limit=10, exclude_active=False):
    facets = h.get_facet_items_dict(facet, limit, exclude_active=exclude_active)
    no_items = c.search_facets.get(facet)['items'].__len__()
    
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
    activity = activity_objects[0]
    return activity.revision_id


def get_last_revision_group(group_id):
#     grp_list  = model.Session.query(model.Group).filter(model.Group.id == group_id).all()
#     grp = grp_list[0]
#     last_rev = grp.all_related_revisions[0][0]
    activity_objects = model.activity.group_activity_list(group_id, limit=1, offset=0)
    activity = activity_objects[0]
    return activity.revision_id

def get_group_followers(grp_id):
    result = logic.get_action('group_follower_count')(
            {'model': model, 'session': model.Session},
            {'id': grp_id})
    return result

def get_group_members(grp_id):
    member_list = logic.get_action('member_list')(
            {'model': model, 'session': model.Session},
            {'id': grp_id})
    result = len(member_list)
    return result

def markdown_extract_strip(text, extract_length=190):
    ''' return the plain text representation of markdown encoded text.  That
    is the texted without any html tags.  If extract_length is 0 then it
    will not be truncated.'''
    result = h.markdown_extract(text, extract_length)
    return result.rstrip('\n')

