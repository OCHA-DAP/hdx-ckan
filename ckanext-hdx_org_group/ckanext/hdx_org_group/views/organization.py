import logging

from flask import Blueprint
from six.moves.urllib.parse import urlencode

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_org_group.helpers.static_lists as static_lists
import ckanext.hdx_theme.helpers.helpers as hdx_helpers

from ckan.views.group import _get_group_template, CreateGroupView
from ckanext.hdx_org_group.controller_logic.organization_read_logic import OrgReadLogic
from ckanext.hdx_org_group.views.light_organization import _index
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed

g = tk.g
config = tk.config
request = tk.request
render = tk.render
redirect = tk.redirect_to
url_for = tk.url_for
get_action = tk.get_action
NotFound = tk.ObjectNotFound
check_access = tk.check_access
NotAuthorized = tk.NotAuthorized
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
    context = {
        'model': model,
        'session': model.Session,
        'for_view': True,
        'with_private': False
    }
    try:
        check_access('site_read', context)
    except NotAuthorized:
        abort(403, _('Not authorized to see this page'))

    try:
        read_logic = OrgReadLogic(id, g.user, g.userobj)
        read_logic.read()
        if read_logic.redirect_result:
            return read_logic.redirect_result

        if read_logic.org_meta.is_custom:
            template_data = _generate_template_data_for_custom_org(read_logic)
            result = render('organization/custom/custom_org.html', template_data)
            return result
        else:
            org_dict = read_logic.org_meta.org_dict
            org_dict.update({
                'search_template_data': read_logic.search_template_data,
                'datasets_num': read_logic.org_meta.datasets_num,
                'allow_req_membership': read_logic.org_meta.allow_req_membership,
                'group_message_info': read_logic.org_meta.group_message_info,
            })

            template_data = {
                'org_dict': org_dict,
            }
            template_file = _get_group_template('read_template', 'organization')
            return render(template_file, template_data)
    except NotFound as e:
        abort(404, _('Page not found'))
    except NotAuthorized as e:
        abort(403, _('Not authorized to see this page'))


def _generate_template_data_for_custom_org(org_read_logic):
    '''
    :param org_read_logic:
    :type org_read_logic: OrgReadLogic
    :returns: the template data dict
    :rtype: dict
    '''
    org_meta = org_read_logic.org_meta
    org_dict = org_meta.org_dict
    org_id = org_dict['id']

    org_dict['group_message_info'] = org_meta.group_message_info
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
            'custom_css_path': org_read_logic.org_meta.custom_css_path,
            # 'member_count': hdx_helpers.get_group_members(org_id),
            'follower_count': org_read_logic.follower_count,
            'top_line_items': org_read_logic.top_line_items,
            # 'search_results': {
            # 'facets': facets,
            # 'activities': activities,
            # 'query_placeholder': query_placeholder
            # },
            'links': {
                'edit': org_read_logic.links.edit,
                'members': org_read_logic.links.members,
                'request_membership': org_read_logic.links.request_membership,
                'add_data': org_read_logic.links.add_data
            },
            'request_params': request.params,
            'permissions': {
                'edit': org_read_logic.allow_edit,
                'add_dataset': org_read_logic.allow_add_dataset,
                'view_members': org_read_logic.allow_basic_user_info,
                'request_membership': org_read_logic.allow_req_membership
            },
            'show_admin_menu': org_read_logic.allow_add_dataset or org_read_logic.allow_edit,
            'show_visualization': 'Choose Visualization Type' != org_read_logic.viz_config['type'],
            'visualization': {
                'config': org_read_logic.viz_config,
                'config_type': org_read_logic.viz_config['type'],
                'config_url': urlencode(org_read_logic.viz_config, True),
                'embed_url': org_read_logic.links.embed_url,
                'basemap_url': config.get('hdx.orgmap.url')
            },

            # This is hear for compatibility with the custom_org_header.html template, which is still
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


def new_org_template_variables(context, data_dict):
    data_dict['hdx_org_type_list'] = [{'value': '-1', 'text': _('-- Please select --')}] + \
                              [{'value': t[1], 'text': _(t[0])} for t in static_lists.ORGANIZATION_TYPE_LIST]



hdx_org.add_url_rule(u'', view_func=index)
hdx_org.add_url_rule(
        u'/new',
        methods=[u'GET', u'POST'],
        view_func=CreateGroupView.as_view(str(u'new')),
        defaults={
            'group_type': 'organization',
            'is_organization': True
        }
)
hdx_org.add_url_rule(u'/<id>', view_func=read)
