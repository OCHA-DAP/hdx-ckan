import logging

from flask import Blueprint
from six.moves.urllib.parse import urlencode

import ckan.lib.plugins as lib_plugins
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_package.helpers.analytics as analytics
import ckanext.hdx_org_group.helpers.analytics as org_analytics
import ckanext.hdx_org_group.helpers.org_meta_dao as org_meta_dao
import ckanext.hdx_org_group.helpers.organization_helper as helper
import ckanext.hdx_org_group.helpers.static_lists as static_lists
import ckanext.hdx_theme.helpers.helpers as hdx_helpers
from ckan.types import Context
from ckan.views.group import CreateGroupView, EditGroupView, _get_group_template
from ckanext.hdx_org_group.controller_logic.organization_read_logic import OrgReadLogic
from ckanext.hdx_org_group.controller_logic.organization_stats_logic import (
    OrganizationStatsLogic,
)
from ckanext.hdx_org_group.views.light_organization import _index
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed
from ckanext.hdx_theme.util.mail import NoRecipientException
from ckanext.hdx_users.general_token_model import ObjectType
from ckanext.hdx_users.helpers.notification_platform import add_unsubscribe_token

g = tk.g
config = tk.config
request = tk.request
render = tk.render
redirect = tk.redirect_to
url_for = tk.url_for
get_action = tk.get_action
check_access = tk.check_access
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError
abort = tk.abort
_ = tk._
h = tk.h

log = logging.getLogger(__name__)

hdx_org = Blueprint(u'hdx_org', __name__, url_prefix=u'/organization')


@check_redirect_needed
def index():
    return _index('organization/index.html', False, True)


@check_redirect_needed
def read(id):
    context: Context = {
        'model': model,
        'session': model.Session,
        'for_view': True,
        'with_private': False
    }

    try:
        read_logic = OrgReadLogic(id, g.user, g.userobj)
        read_logic.read()
        if read_logic.redirect_result:
            return read_logic.redirect_result

        # Standard and custom orgs render the same unified v2 template (task 056)
        org_dict = read_logic.org_meta.org_dict
        org_dict.update({
            'search_template_data': read_logic.search_template_data,
            'datasets_num': read_logic.search_template_data.get('facets').get('extras_archived').get('fals'),
            'archived_package_count': read_logic.search_template_data.get('facets').get('extras_archived').get('true'),
            'allow_req_membership': read_logic.org_meta.allow_req_membership,
            # 'group_message_info': read_logic.org_meta.group_message_info,
        })

        template_data = {
            'org_dict': org_dict,
            'org_meta': read_logic.org_meta,
            'analytics': {
                'analytics_came_from': analytics.came_from(request.args),
                'analytics_supports_notifications': analytics.supports_notifications(ObjectType.ORGANIZATION,
                                                                                     org_dict),
            }
        }
        unsubscribe_token = request.args.get('_unsubscribe_token', None)
        add_unsubscribe_token(unsubscribe_token, ObjectType.ORGANIZATION, org_dict.get('id'), template_data)
        template_file = _get_group_template('read_template', 'organization')
        return render(template_file, template_data)
    except NotFound:
        abort(404, _('Page not found'))
    except NotAuthorized:
        abort(403, _('Not authorized to see this page'))


def _generate_template_data_for_custom_org(org_read_logic):
    """
    :param org_read_logic:
    :type org_read_logic: OrgReadLogic
    :returns: the template data dict
    :rtype: dict
    """
    org_meta = org_read_logic.org_meta
    org_dict = org_meta.org_dict
    org_id = org_dict['id']

    # org_dict['group_message_info'] = org_meta.group_message_info
    template_data = {
        'data': {
            'org_info': {
                'id': org_id,
                'display_name': org_dict.get('display_name', ''),
                'description': org_dict.get('description'),
                'name': org_dict['name'],
                'link': org_dict.get('extras', {}).get('org_url'),
                # 'topline_resource': org_meta.customization.get('topline_resource'),
                'modified_at': org_dict.get('modified_at', ''),
                'image_sq': org_meta.customization.get('image_sq'),
                'image_rect': org_meta.customization.get('image_rect'),
                # 'visualization_config': result.get('visualization_config', ''),
            },
            'search_template_data': org_read_logic.search_template_data,
            #'custom_css_path': org_read_logic.org_meta.custom_css_path,
            # 'member_count': hdx_helpers.get_group_members(org_id),
            'follower_count': org_read_logic.follower_count,
            'top_line_items': org_read_logic.top_line_items,
            # 'search_results': {
            # 'facets': facets,
            # 'activities': activities,
            # 'query_placeholder': query_placeholder
            # },
            # 'links': {
            #     'edit': org_read_logic.links.edit,
            #     'members': org_read_logic.links.members,
            #     'request_membership': org_read_logic.links.request_membership,
            #     'add_data': org_read_logic.links.add_data
            # },
            'request_params': request.args,
            'permissions': {
                'edit': org_read_logic.allow_edit,
                'add_dataset': org_read_logic.allow_add_dataset,
                'view_members': org_read_logic.allow_basic_user_info,
                'request_membership': org_read_logic.allow_req_membership
            },
            'show_admin_menu': org_read_logic.allow_add_dataset or org_read_logic.allow_edit,
            'show_visualization': 'Choose Visualization Type' != org_read_logic.viz_config.get('type'),
            'visualization': {
                'config': org_read_logic.viz_config,
                'config_type': org_read_logic.viz_config.get('type'),
                'config_url': urlencode(org_read_logic.viz_config, True),
                # 'embed_url': org_read_logic.links.embed_url,

            },

            # This is here for compatibility with the custom_org_header.html template, which is still
            # used from pylon controllers
            'org_meta': {
                'id': org_dict['name'],
                'custom_rect_logo_url': org_meta.custom_rect_logo_url,
                'custom_sq_logo_url': org_meta.custom_sq_logo_url,
                'followers_num': org_meta.followers_num,
                'members_num': org_meta.members_num,
                'allow_req_membership': org_meta.allow_req_membership,
                'allow_basic_user_info': org_meta.allow_basic_user_info,
                'allow_add_dataset': org_meta.allow_add_dataset,
                'allow_edit': org_meta.allow_edit,
                'org_dict': org_dict,
            },

        },
        'errors': org_read_logic.errors,
        'error_summary': org_read_logic.error_summary,

    }
    if template_data['data']['show_visualization']:
        template_data['data']['show_visualization'] = \
            hdx_helpers.check_all_str_fields_not_empty(template_data['data']['visualization'],
                                                       'Visualization config field "{}" is empty',
                                                       skipped_keys=['config'],
                                                       errors=template_data['errors'])
    return template_data


def new_org_template_variables(data_dict):
    data_dict['hdx_org_type_list'] = [{'value': '-1', 'text': _('-- Please select --')}] + \
                              [{'value': t[1], 'text': _(t[0])} for t in static_lists.ORGANIZATION_TYPE_LIST]


def stats(id):
    stats_logic = OrganizationStatsLogic(id, g.user, g.userobj)
    org_dict = stats_logic.org_meta_dao.org_dict
    org_dict.update({
        'allow_req_membership': stats_logic.org_meta_dao.allow_req_membership,
        # 'group_message_info': stats_logic.org_meta_dao.group_message_info,
    })
    template_data = {
        'data': stats_logic.fetch_stats(),
        'org_meta': stats_logic.org_meta_dao,
        'org_dict': org_dict,
    }

    if stats_logic.is_custom():
        return render('organization/custom_stats.html', template_data)
    else:
        return render('organization/stats.html', template_data)


def restore(id):
    context: Context = {
        'model': model, 'session': model.Session,
        'user': g.user,
        'for_edit': True,
    }

    try:
        check_access('organization_patch', context, {'id': id})
    except NotAuthorized:
        return abort(403, _('Unauthorized to restore this organization'))

    try:
        get_action('organization_patch')(context, {
            'id': id,
            'state': 'active'
        })
        return redirect('organization.read', id=id)
    except NotAuthorized:
        return abort(403, _('Unauthorized to read group %s') % id)
    except NotFound:
        return abort(404, _('Group not found'))
    except ValidationError as e:
        errors = e.error_dict
        error_summary = e.error_summary
        core_view = EditGroupView()
        return core_view.get(id, 'organization', True, errors=errors, error_summary=error_summary)


def activity(id):
    return activity_offset(id)


def activity_offset(id, offset=0):
    """
     Modified core functionality to use the new OrgMetaDao class
    for fetching information needed on all org-related pages.

    Render this group's public activity stream page.

    :param id:
    :type id: str
    :param offset:
    :type offset: int
    :return:
    """
    org_meta = org_meta_dao.OrgMetaDao(id, g.user, g.userobj)
    org_meta.fetch_all()
    org_dict = org_meta.org_dict
    # org_dict['group_message_info'] = org_meta.group_message_info

    helper.org_add_last_updated_field([org_dict])

    # Add the group's activity stream (already rendered to HTML) to the
    # template context for the group/read.html template to retrieve later.
    context: Context = {'model': model, 'session': model.Session,
               'user': g.user, 'for_view': True}
    group_activity_stream = get_action('organization_activity_list')(
        context, {'id': org_dict['id'], 'offset': offset})

    extra_vars = {
        'org_dict': org_dict,
        'org_meta': org_meta,
        'group_activity_stream': group_activity_stream,

    }
    if org_meta.is_custom:
        template = 'organization/custom_activity_stream.html'
    else:
        template = lib_plugins.lookup_group_plugin('organization').activity_template()
    return render(template, extra_vars)

def download_organization_stats(id):
    """
        Handles downloading .xlsx organization stats

        :returns: xlsx
    """

    context: Context = {
        'model': model,
        'session': model.Session,
        'user': g.user or g.author,
        'auth_user_obj': g.userobj
    }

    try:
        check_access('organization_update', context, {'id': id})
    except NotAuthorized:
        return abort(403, _('Unauthorized to restore this organization'))

    # check if organization exists
    try:
        org_dict = get_action('organization_show')(context, {'id': id})
        output = helper.hdx_generate_organization_stats(org_dict)
        org_analytics.OrganizationStatsDownloadAnalyticsSender(org_dict.get('name', ''), org_dict.get('id', '')) \
            .send_to_queue()
        return output

    except NotFound:
        return abort(404, _('Organization not found'))
    except NotAuthorized:
        return abort(404, _('Organization not found'))
    except Exception as e:
        log.error(e)
        return abort(404, _('Something went wrong, please contact us'))


hdx_org.add_url_rule(u'/', view_func=index, strict_slashes=False)
hdx_org.add_url_rule(
        u'/new',
        methods=[u'GET', u'POST'],
        view_func=CreateGroupView.as_view(str(u'new')),
        defaults={
            'group_type': 'organization',
            'is_organization': True
        }
)
# hdx_org.add_url_rule(u'/request_new', view_func=request_new, methods=[u'GET', u'POST'])
hdx_org.add_url_rule(u'/<id>', view_func=read)
hdx_org.add_url_rule(u'/stats/<id>', view_func=stats)
hdx_org.add_url_rule(u'/restore/<id>', view_func=restore, methods=[u'POST'])
hdx_org.add_url_rule(u'/activity/<id>', view_func=activity)
hdx_org.add_url_rule(u'/activity/<id>/<int:offset>', view_func=activity_offset, defaults={'offset': 0})
hdx_org.add_url_rule(u'/<id>/download_stats', view_func=download_organization_stats)
