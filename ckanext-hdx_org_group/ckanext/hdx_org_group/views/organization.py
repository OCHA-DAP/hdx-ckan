import logging

from flask import Blueprint
from six.moves.urllib.parse import urlencode

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.lib.plugins as lib_plugins

import ckanext.hdx_org_group.helpers.org_meta_dao as org_meta_dao
import ckanext.hdx_org_group.helpers.organization_helper as helper
import ckanext.hdx_org_group.helpers.static_lists as static_lists
import ckanext.hdx_theme.helpers.helpers as hdx_helpers

from ckan.views.group import _get_group_template, CreateGroupView, EditGroupView
from ckanext.hdx_org_group.controller_logic.organization_read_logic import OrgReadLogic
from ckanext.hdx_org_group.controller_logic.organization_stats_logic import OrganizationStatsLogic
from ckanext.hdx_org_group.views.light_organization import _index
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed
from ckanext.hdx_theme.util.mail import NoRecipientException

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
                'datasets_num': read_logic.search_template_data.get('facets').get('extras_archived').get('fals'),
                'archived_package_count': read_logic.search_template_data.get('facets').get('extras_archived').get('true'),
                'allow_req_membership': read_logic.org_meta.allow_req_membership,
                # 'group_message_info': read_logic.org_meta.group_message_info,
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
                # 'embed_url': org_read_logic.links.embed_url,

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


def request_new():
    context = {'model': model, 'session': model.Session, 'user': g.user}
    try:
        check_access('hdx_send_new_org_request', context)
    except NotAuthorized:
        abort(403, _('Unauthorized to send a new org request'))

    errors = {}
    error_summary = {}
    data = {'from': request.form.get('from', '')}

    sent_successfully = False
    if 'save' in request.form and request.method == 'POST':
        try:
            data = _process_new_org_request()
            _validate_new_org_request_field(data)

            get_action('hdx_send_new_org_request')(context, _transform_dict_for_mailing(data))

            data.clear()
            h.flash_success(_('Request sent successfully'))
            sent_successfully = True
        except NoRecipientException as e:
            h.flash_error(_(str(e)))
        except ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary
        except Exception as e:
            log.error(str(e))
            h.flash_error(_('Request can not be sent. Contact an administrator'))
        if sent_successfully:
            return h.redirect_to('dashboard.organizations')

    hdx_org_type_list = [{'value': '-1', 'text': _('-- Please select --')}] + \
                        [{'value': t[1], 'text': _(t[0])} for t in static_lists.ORGANIZATION_TYPE_LIST]
    template_data = {
        'data': {
            'action': 'new',
            'hdx_org_type_list': hdx_org_type_list
        },
        'form_data': data,
        'errors': errors,
        'error_summary': error_summary,

    }
    g.form = render('organization/request_organization_form.html', template_data)
    return render('organization/request_new.html')


def _process_new_org_request():
    hdx_org_type = None
    hdx_org_type_code = request.form.get('hdx_org_type', '')

    if hdx_org_type_code:
        hdx_org_type = next(
            (type[0] for type in static_lists.ORGANIZATION_TYPE_LIST if type[1] == hdx_org_type_code), '-1')

    data = {
        'name': request.form.get('name', ''),
        'title': request.form.get('title', ''),
        'org_url': request.form.get('org_url', ''),
        'description': request.form.get('description', ''),
        'your_email': request.form.get('your_email', ''),
        'your_name': request.form.get('your_name', ''),
        'org_acronym': request.form.get('org_acronym', ''),
        'hdx_org_type': hdx_org_type,
        'hdx_org_type_code': hdx_org_type_code,  # This is needed for the form when validation fails
    }
    return data


def _validate_new_org_request_field(data):
    errors = {}
    for field in ['title', 'description', 'your_email', 'your_name', 'hdx_org_type']:
        if data[field].strip() in ['', '-1']:
            errors[field] = [_('should not be empty')]

    if len(errors) > 0:
        raise ValidationError(errors)


def _transform_dict_for_mailing(data_dict):
    data_dict_for_mailing = {
        'name': data_dict.get('title'),
        'acronym': data_dict.get('org_acronym'),
        'description': data_dict.get('description'),
        'org_type': data_dict.get('hdx_org_type', ''),
        'org_url': data_dict.get('org_url', ''),

        'work_email': data_dict.get('your_email', ''),
        'your_name': data_dict.get('your_name', ''),
    }
    return data_dict_for_mailing


def new_org_template_variables(context, data_dict):
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
    context = {
        'model': model, 'session': model.Session,
        'user': g.user,
        'for_edit': True,
    }

    try:
        check_access('organization_patch', context, {'id': id})
    except NotAuthorized as e:
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
    '''
     Modified core functionality to use the new OrgMetaDao class
    for fetching information needed on all org-related pages.

    Render this group's public activity stream page.

    :param id:
    :type id: str
    :param offset:
    :type offset: int
    :return:
    '''
    org_meta = org_meta_dao.OrgMetaDao(id, g.user, g.userobj)
    org_meta.fetch_all()
    org_dict = org_meta.org_dict
    # org_dict['group_message_info'] = org_meta.group_message_info

    helper.org_add_last_updated_field([org_dict])

    # Add the group's activity stream (already rendered to HTML) to the
    # template context for the group/read.html template to retrieve later.
    context = {'model': model, 'session': model.Session,
               'user': g.user, 'for_view': True}
    group_activity_stream = get_action('organization_activity_list')(
        context, {'id': org_dict['id'], 'offset': offset})



    extra_vars = {
        'org_dict': org_dict,
        'org_meta': org_meta,
        'group_activity_stream': group_activity_stream,

    }
    template = None
    if org_meta.is_custom:
        template = 'organization/custom_activity_stream.html'
    else:
        template = lib_plugins.lookup_group_plugin('organization').activity_template()
    return render(template, extra_vars)


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
hdx_org.add_url_rule(u'/request_new', view_func=request_new, methods=[u'GET', u'POST'])
hdx_org.add_url_rule(u'/<id>', view_func=read)
hdx_org.add_url_rule(u'/stats/<id>', view_func=stats)
hdx_org.add_url_rule(u'/restore/<id>', view_func=restore, methods=[u'POST'])
hdx_org.add_url_rule(u'/activity/<id>', view_func=activity)
hdx_org.add_url_rule(u'/activity/<id>/<int:offset>', view_func=activity_offset, defaults={'offset': 0})
