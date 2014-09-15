import re
import ckan.lib.helpers as h
from ckan.common import (
     c, request
)
import sqlalchemy
import ckan.model as model
import ckan.lib.base as base
import ckan.logic as logic
import datetime
import json
import logging
import ckan.plugins.toolkit as tk
import re
import ckan.new_authz as new_authz
import ckan.lib.activity_streams as activity_streams
import ckan.model.package as package
import ckan.model.misc as misc

import ckanext.hdx_theme.helpers.counting_actions as counting

from webhelpers.html import escape, HTML, literal, url_escape
from ckan.common import _

get_action = logic.get_action
log = logging.getLogger(__name__)
_check_access = logic.check_access
_get_or_bust = logic.get_or_bust
NotFound = logic.NotFound


def hdx_user_org_num(user_id):
    context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author}
    try:
        user    = tk.get_action('organization_list_for_user')(context,{'id':user_id, 'permission': 'create_dataset'})
    except logic.NotAuthorized:
            base.abort(401, _('Unauthorized to see organization member list'))    
        
    return user

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


def hdx_get_activity_list(context, data_dict):
    activity_stream = get_action('package_activity_list')(context, data_dict)
    #activity_stream = package_activity_list(context, data_dict)
    offset = int(data_dict.get('offset', 0))
    extra_vars = {
        'controller': 'package',
        'action': 'activity',
        'id': data_dict['id'],
        'offset': offset,
        }
    return _activity_list(context, activity_stream, extra_vars)


def hdx_find_license_name(license_id, license_name):
    if license_name == None or len(license_name) == 0 or license_name == license_id:
        original_license_list = (
            l.as_dict() for l in package.Package._license_register.licenses)
        license_dict = {l['id']: l['title']
                        for l in original_license_list}
        if license_id in license_dict:
            return license_dict[license_id]
    return license_name


#code copied from activity_streams.activity_list_to_html and modified to return only the activity list
def _activity_list(context, activity_stream, extra_vars):
    '''Return the given activity stream 

    :param activity_stream: the activity stream to render
    :type activity_stream: list of activity dictionaries
    :param extra_vars: extra variables to pass to the activity stream items
        template when rendering it
    :type extra_vars: dictionary


    '''
    activity_list = [] # These are the activity stream messages.
    for activity in activity_stream:
        detail = None
        activity_type = activity['activity_type']
        # Some activity types may have details.
        if activity_type in activity_streams.activity_stream_actions_with_detail:
            details = logic.get_action('activity_detail_list')(context=context,
                data_dict={'id': activity['id']})
            # If an activity has just one activity detail then render the
            # detail instead of the activity.
            if len(details) == 1:
                detail = details[0]
                object_type = detail['object_type']

                if object_type == 'PackageExtra':
                    object_type = 'package_extra'

                new_activity_type = '%s %s' % (detail['activity_type'],
                                            object_type.lower())
                if new_activity_type in activity_streams.activity_stream_string_functions:
                    activity_type = new_activity_type

        if not activity_type in activity_streams.activity_stream_string_functions:
            raise NotImplementedError("No activity renderer for activity "
                "type '%s'" % activity_type)

        if activity_type in activity_streams.activity_stream_string_icons:
            activity_icon = activity_streams.activity_stream_string_icons[activity_type]
        else:
            activity_icon = activity_streams.activity_stream_string_icons['undefined']

        activity_msg = activity_streams.activity_stream_string_functions[activity_type](context,
                activity)

        # Get the data needed to render the message.
        matches = re.findall('\{([^}]*)\}', activity_msg)
        data = {}
        for match in matches:
            snippet = activity_streams.activity_snippet_functions[match](activity, detail)
            data[str(match)] = snippet

        activity_list.append({'msg': activity_msg,
                              'type': activity_type.replace(' ', '-').lower(),
                              'icon': activity_icon,
                              'data': data,
                              'timestamp': activity['timestamp'],
                              'is_new': activity.get('is_new', False)})
    extra_vars['activities'] = activity_list
    return extra_vars


def hdx_tag_autocomplete(context, data_dict):
    '''Return a list of tag names that contain a given string.

    By default only free tags (tags that don't belong to any vocabulary) are
    searched. If the ``vocabulary_id`` argument is given then only tags
    belonging to that vocabulary will be searched instead.

    :param query: the string to search for
    :type query: string
    :param vocabulary_id: the id or name of the tag vocabulary to search in
      (optional)
    :type vocabulary_id: string
    :param fields: deprecated
    :type fields: dictionary
    :param limit: the maximum number of tags to return
    :type limit: int
    :param offset: when ``limit`` is given, the offset to start returning tags
        from
    :type offset: int

    :rtype: list of strings

    '''
    _check_access('tag_autocomplete', context, data_dict)
    matching_tags, count = _tag_search(context, data_dict)
    if matching_tags:
        return [tag.name for tag in matching_tags]
    else:
        return []
   
#code copied from get.py line 1748 
def _tag_search(context, data_dict):
    model = context['model']

    terms = data_dict.get('query') or data_dict.get('q') or []
    if isinstance(terms, basestring):
        terms = [terms]
    terms = [ t.strip() for t in terms if t.strip() ]

    if 'fields' in data_dict:
        log.warning('"fields" parameter is deprecated.  '
                    'Use the "query" parameter instead')

    fields = data_dict.get('fields', {})
    offset = data_dict.get('offset')
    limit = data_dict.get('limit')

    # TODO: should we check for user authentication first?
    q = model.Session.query(model.Tag)

    #CHANGES to initial version
#     if 'vocabulary_id' in data_dict:
#         # Filter by vocabulary.
#         vocab = model.Vocabulary.get(_get_or_bust(data_dict, 'vocabulary_id'))
#         if not vocab:
#             raise NotFound
#         q = q.filter(model.Tag.vocabulary_id == vocab.id)
#     else:
#         # If no vocabulary_name in data dict then show free tags only.
#         q = q.filter(model.Tag.vocabulary_id == None)
#         # If we're searching free tags, limit results to tags that are
#         # currently applied to a package.
#         q = q.distinct().join(model.Tag.package_tags)

    for field, value in fields.items():
        if field in ('tag', 'tags'):
            terms.append(value)

    if not len(terms):
        return [], 0

    for term in terms:
        escaped_term = misc.escape_sql_like_special_characters(term, escape='\\')
        q = q.filter(model.Tag.name.ilike('%' + escaped_term + '%'))

    count = q.count()
    q = q.offset(offset)
    q = q.limit(limit)
    return q.all(), count   