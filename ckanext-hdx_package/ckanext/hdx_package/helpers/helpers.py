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

import ckanext.hdx_theme.helpers.counting_actions as counting

from webhelpers.html import escape, HTML, literal, url_escape
from ckan.common import _

get_action = logic.get_action
log = logging.getLogger(__name__)


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