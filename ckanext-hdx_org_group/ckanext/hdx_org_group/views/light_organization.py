from flask import Blueprint

import logging
import ckan.logic as logic
import ckan.common as common
import ckan.model as model
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk


import ckanext.hdx_org_group.helpers.organization_helper as helper
from ckanext.hdx_org_group.controller_logic.organization_read_logic import LightOrgReadLogic
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed

g = common.g
request = common.request

get_action = tk.get_action
check_access = tk.check_access
render = tk.render
abort = tk.abort
redirect = tk.redirect_to
NotAuthorized = tk.NotAuthorized
NotFound = logic.NotFound
_ = tk._

log = logging.getLogger(__name__)


hdx_light_org = Blueprint(u'hdx_light_org', __name__, url_prefix=u'/m/organization')


@check_redirect_needed
def index():
    return _index('organization/index.html', False, True)


@check_redirect_needed
def light_index():
    return _index('light/organization/index.html', True, False)


def _index(template_file, show_switch_to_desktop, show_switch_to_mobile):
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
    # pass user info to context as needed to view private datasets of
    # orgs correctly
    # if c.userobj:
    #     context['user_id'] = c.userobj.id
    #     context['user_is_admin'] = c.userobj.sysadmin
    #     context['auth_user_obj'] = c.userobj
    try:
        q = request.params.get('q', '')
        page = int(request.params.get('page', 1))
        limit = int(request.params.get('limit', 25))
        sort_option = request.params.get('sort', 'title asc')
    except ValueError:
        abort(404, 'Page not found')
        sort_option = ''
        q = ''
    # reset_thumbnails = request.params.get('reset_thumbnails', 'false')
    # data_dict = {
    #     'all_fields': True,
    #     'sort': sort_option if sort_option in ['title asc', 'title desc'] else 'title asc',
    #     # Custom sorts will throw an error here
    #     'q': q,
    #     # 'reset_thumbnails': reset_thumbnails,
    # }
    all_orgs = get_action('cached_organization_list')(context, {})
    all_orgs = helper.filter_and_sort_results_case_insensitive(all_orgs, sort_option, q=q, has_datasets=True)

    # c.featured_orgs = helper.hdx_get_featured_orgs(context, data_dict)
    def pager_url(page=None):
        if sort_option:
            url = h.url_for(
                'organizations_index', q=q, page=page, sort=sort_option, limit=limit) + '#organizationsSection'
        else:
            url = h.url_for('organizations_index', q=q, page=page, limit=limit) + '#organizationsSection'
        return url

    page = h.Page(
        collection=all_orgs,
        page=page,
        url=pager_url,
        items_per_page=limit
    )
    # displayed_orgs = c.featured_orgs + [o for o in c.page]
    displayed_orgs = [o for o in page]
    helper.org_add_last_updated_field(displayed_orgs)
    template_data = {
        'q': q,
        'sorting_selected': sort_option,
        'limit_selected': limit,
        'page': page,
        'page_has_desktop_version': show_switch_to_desktop,
        'page_has_mobile_version': show_switch_to_mobile,
    }
    return render(template_file, template_data)


@check_redirect_needed
def light_read(id):
    return _read('light/organization/read.html', id, True, False)


def _read(template_file, id, show_switch_to_desktop, show_switch_to_mobile):
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
        read_logic = LightOrgReadLogic(id, g.user, g.userobj)
        read_logic.read()
        if read_logic.redirect_result:
            return read_logic.redirect_result

        org_dict = read_logic.org_meta.org_dict
        org_dict.update({
            'template_data': read_logic.search_template_data,
            'datasets_num': read_logic.org_meta.datasets_num,
            'custom_sq_logo_url': read_logic.org_meta.custom_sq_logo_url,
        })

        template_data = {
            'org_dict': org_dict,
            'page_has_desktop_version': show_switch_to_desktop,
            'page_has_mobile_version': show_switch_to_mobile,
        }
        return render(template_file, template_data)
    except NotFound as e:
        abort(404, _('Page not found'))
    except NotAuthorized as e:
        abort(403, _('Not authorized to see this page'))


@check_redirect_needed
def light_fake(id):
    return redirect('hdx_light_org.light_read', id=id)


hdx_light_org.add_url_rule(u'', view_func=light_index)
hdx_light_org.add_url_rule(u'/<id>', view_func=light_read)
hdx_light_org.add_url_rule(u'/activity/<id>', view_func=light_fake)
hdx_light_org.add_url_rule(u'/stats/<id>', view_func=light_fake)
hdx_light_org.add_url_rule(u'/members/<id>', view_func=light_fake)
hdx_light_org.add_url_rule(u'/requested_data/<id>', view_func=light_fake)
