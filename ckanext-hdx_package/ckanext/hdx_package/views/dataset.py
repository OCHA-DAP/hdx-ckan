import json
import logging

from flask import Blueprint

import ckan.authz as authz
import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_package.helpers.analytics as analytics
import ckanext.hdx_package.helpers.custom_pages as cp_h
import ckanext.hdx_package.helpers.custom_validator as vd
import ckanext.hdx_package.helpers.membership_data as membership_data
import ckanext.hdx_search.helpers.search_history as search_history
import ckanext.hdx_package.controller_logic.dataset_view_logic as dataset_view_logic

from ckan.views.dataset import _setup_template_variables

from ckanext.hdx_package.helpers import resource_grouping
from ckanext.hdx_package.helpers.util import find_approx_download
from ckanext.hdx_package.views.light_dataset import generic_search
from ckanext.hdx_search.controller_logic.qa_logs_logic import QALogsLogic
from ckanext.hdx_theme.util.jql import fetch_downloads_per_week_for_dataset
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed

log = logging.getLogger(__name__)

config = tk.config
get_action = tk.get_action
check_access = tk.check_access
request = tk.request
render = tk.render
abort = tk.abort
redirect = tk.redirect_to
_ = tk._
h = tk.h
g = tk.g

NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound

hdx_dataset = Blueprint(u'hdx_dataset', __name__, url_prefix=u'/dataset')
hdx_search = Blueprint(u'hdx_search', __name__, url_prefix=u'/search')


@check_redirect_needed
def search():
    query_string = request.args.get('q', u'')
    if g.userobj and query_string:
        search_history.store_search(query_string, g.userobj.id)
    return generic_search(u'search/search.html')


def qa_pii_log(id, resource_id, file_name):
    qa_logs_logic = QALogsLogic(resource_id, file_name).read()

    if request.args.get("noredirect"):
        return qa_logs_logic.url
    else:
        return redirect(qa_logs_logic.url)


def qa_sdcmicro_log(id, resource_id):
    qa_logs_logic = QALogsLogic(resource_id, 'sdc.log.txt').read()
    return redirect(qa_logs_logic.url)


@check_redirect_needed
def read(id):
    """
    Display the package, includes HDX additions for continuous browsing
    """

    context = {'model': model, 'session': model.Session,
               'user': g.user, 'for_view': True,
               'auth_user_obj': g.userobj}
    data_dict = {'id': id, 'include_tracking': True}

    # check if package exists
    try:
        pkg_dict = get_action('package_show')(context, data_dict)
        pkg = context['package']

        showcase_list = []
        # Needed because of showcase validation convert_package_name_or_id_to_id_for_type_dataset()
        current_pkg_type = pkg_dict.get('type')

        if current_pkg_type == 'dataset':
            context_showcase = {'model': model, 'session': model.Session,
                       'user': g.user, 'for_view': True,
                       'auth_user_obj': g.userobj}
            _showcase_list = get_action('ckanext_package_showcase_list')(context_showcase,
                                                                         {'package_id': pkg_dict['id']})
            if _showcase_list:
                showcase_list = sorted(_showcase_list, key=lambda i: i.get('metadata_modified'), reverse=True)
            pkg_dict['showcase_count'] = len(_showcase_list)
        else:
            return abort(404, _('Package type is not dataset'))
    except (NotFound, NotAuthorized):
        return abort(404, _('Dataset not found'))

    log.debug('Reading dataset {}: checking which resources can be previewed'.format(pkg_dict.get('name')))
    # can the resources be previewed?
    for resource in pkg_dict['resources']:
        resource_views = [] if resource.get('in_quarantine') is True else get_action('resource_view_list')(context, {
            'id': resource['id']})
        resource['has_views'] = bool(_find_default_view(resource, resource_views))
        resource['resource_views'] = resource_views

        # if helpers.is_ckan_domain(resource['url']):
        #     resource['url'] = helpers.make_url_relative(resource['url'])
        #
        # if resource.get('perma_link') and helpers.is_ckan_domain(resource['perma_link']):
        #     resource['perma_link'] = helpers.make_url_relative(resource['perma_link'])

    # dealing with resource grouping
    resource_grouping.set_show_groupings_flag(pkg_dict)
    if pkg_dict.get('x_show_grouping'):
        resource_grouping.add_other_grouping_if_needed(pkg_dict)

    package_type = pkg_dict['type'] or 'dataset'
    _setup_template_variables(context, {'id': id}, package_type=package_type)

    # package_saver.PackageSaver().render_package(c.pkg_dict, context)

    log.debug('Reading dataset {}: setting analytics data for template'.format(pkg_dict.get('name')))
    # set dataset type for google analytics - modified by HDX
    analytics_is_cod = analytics.is_cod(pkg_dict)
    # c.analytics_is_indicator = analytics.is_indicator(c.pkg_dict)
    analytics_is_archived = analytics.is_archived(pkg_dict)
    analytics_group_names, analytics_group_ids = analytics.extract_locations_in_json(pkg_dict)
    analytics_dataset_availability = analytics.dataset_availability(pkg_dict)

    # changes done for indicator
    act_data_dict = {'id': pkg_dict['id'], 'limit': 7}
    log.debug('Reading dataset {}: getting activity list for dataset'.format(pkg_dict.get('name')))

    hdx_activities = get_action(u'package_activity_list')(context, act_data_dict)

    pkg_dict['approx_total_downloads'] = find_approx_download(pkg_dict.get('total_res_downloads', 0))

    # Constructing the email body
    log.debug('Reading dataset {}: constructing email body'.format(pkg_dict.get('name')))
    notes = pkg_dict.get('notes') if pkg_dict.get('notes') else _('No description available')
    pkg_dict['social_mail_body'] = _('Description:%0D%0A') + h.markdown_extract(
        notes) + ' %0D%0A'

    membership = membership_data.get_membership_by_user(g.user or g.author, pkg.owner_org, g.userobj)

    user_has_edit_rights = h.check_access('package_update', {'id': pkg_dict['id']})

    # analytics charts
    log.debug('Reading dataset {}: getting data for analytics charts'.format(pkg_dict.get('name')))
    downloads_last_weeks = fetch_downloads_per_week_for_dataset(pkg_dict['id']).values()
    stats_downloads_last_weeks = list(downloads_last_weeks)

    # tags&custom_pages
    log.debug('Reading dataset {}: finding custom page list for this dataset'.format(pkg_dict.get('name')))
    pkg_dict['page_list'] = cp_h.hdx_get_page_list_for_dataset(context, pkg_dict)

    # links to vizualizations
    log.debug('Reading dataset {}: finding links list for this dataset'.format(pkg_dict.get('name')))
    pkg_dict['links_list'] = get_action('hdx_package_links_by_id_list')(context, {'id': pkg_dict.get('name')})

    log.debug('Reading dataset {}: deciding on the dataset visualization/preview'.format(pkg_dict.get('name')))
    _dataset_preview = None
    if 'resources' in pkg_dict:
        _dataset_preview = pkg_dict.get('dataset_preview', vd._DATASET_PREVIEW_FIRST_RESOURCE)

    org_dict = pkg_dict.get('organization') or {}
    org_id = org_dict.get('id', None)
    org_info_dict = _get_org_extras(org_id)
    user_survey_url = org_info_dict.get('user_survey_url')
    pkg_dict['user_survey_url'] = user_survey_url
    if org_info_dict.get('custom_org', False):
        logo_config = _process_customizations(org_info_dict.get('customization', None))
    else:
        logo_config = {}

    template_data = {
        'pkg_dict': pkg_dict,
        'pkg': pkg,
        'showcase_list': showcase_list,
        'hdx_activities': hdx_activities,
        'membership': membership,
        'user_has_edit_rights': user_has_edit_rights,
        'analytics_is_cod': analytics_is_cod,
        'analytics_is_indicator': 'false',
        'analytics_is_archived': analytics_is_archived,
        'analytics_group_names': analytics_group_names,
        'analytics_group_ids': analytics_group_ids,
        'analytics_dataset_availability': analytics_dataset_availability,
        'stats_downloads_last_weeks': stats_downloads_last_weeks,
        'user_survey_url': user_survey_url,
        'logo_config': logo_config,
    }

    if _dataset_preview != vd._DATASET_PREVIEW_NO_PREVIEW:
        view_enabled_resources = [r for r in pkg_dict['resources'] if
                                  r.get('no_preview') != 'true' and r.get('in_quarantine') is not True]
        dataset_preview_enabled_list = []
        dataset_preview_disabled_list = []
        if _dataset_preview == vd._DATASET_PREVIEW_RESOURCE_ID:
            for r in view_enabled_resources:
                if r.get('dataset_preview_enabled') == 'True':
                    dataset_preview_enabled_list.append(r)
                else:
                    dataset_preview_disabled_list.append(r)
            dataset_preview_enabled_list.extend(dataset_preview_disabled_list)
            view_enabled_resources = dataset_preview_enabled_list
        for r in view_enabled_resources:
            _res_view = _check_resource(r)
            if _res_view is None:
                continue
            if _res_view.get('type') == 'hdx_geo_preview':
                template_data['shapes'] = json.dumps(
                    dataset_view_logic.process_shapes(pkg_dict['resources'], r.get('id')))
                return render('package/hdx-read-shape.html', template_data)
            if _res_view.get('type') == 'hdx_hxl_preview':
                template_data['default_view'] = _res_view
                has_modify_permission = authz.is_authorized_boolean('package_update', context, {'id': pkg_dict['id']})
                template_data['hxl_preview_urls'] = {
                    'onlyView': get_action('hxl_preview_iframe_url_show')({
                        'has_modify_permission': has_modify_permission
                    }, {
                        'resource': _res_view.get('resource'),
                        'resource_view': _res_view.get('view'),
                        'hxl_preview_mode': 'onlyView'
                    })
                    # 'edit': get_action('hxl_preview_iframe_url_show')({}, {
                    #     'resource': _default_view.get('resource'),
                    #     'resource_view': _default_view.get('view'),
                    #     'hxl_preview_mode': 'edit'
                    # })
                }
                return render('package/hdx-read-hxl.html', template_data)

    log.debug('Reading dataset {}: rendering template'.format(pkg_dict.get('name')))
    if org_info_dict.get('custom_org', False):
        return render('package/custom_hdx_read.html', template_data)
    return render('package/hdx_read.html', template_data)


def _get_org_extras(org_id):
    """
    Get the extras for our orgs
    """
    if not org_id:
        return {}
    context = {'model': model, 'session': model.Session,
               'user': g.user or g.author,
               'include_datasets': False,
               'for_view': True}
    data_dict = {'id': org_id}
    org_info = get_action(
        'hdx_light_group_show')(context, data_dict)

    extras_dict = {item['key']: item['value'] for item in org_info.get('extras', {})}
    extras_dict['image_url'] = org_info.get('image_url', None)

    return extras_dict


def _process_customizations(json_string):
    """
    Process settings for datasets belonging to custom layouts
    """
    logo_config = {
        'logo_bg_color': '',
        'highlight_color': '',
        'custom_org': True
    }
    if json_string:
        custom_dict = json.loads(json_string)
        highlight_color = custom_dict.get('highlight_color', None)
        if highlight_color:
            logo_config['highlight_color'] = highlight_color
        logo_bg_color = custom_dict.get('logo_bg_color', None)
        if logo_bg_color:
            logo_config['logo_bg_color'] = logo_bg_color
        image_name = custom_dict.get('image_rect', None)
        if image_name:
            logo_config['image_url'] = h.url_for('hdx_local_image_server.org_file', filename=image_name)

    return logo_config


def _find_default_view(resource, resource_views):
    default_resource_view = resource_views[0] if resource_views else None
    res_format = (resource.get('format', None) or '').lower()
    if 'xlsx' in res_format:
        default_resource_view = next(
            (rv for rv in resource_views if rv.get('view_type') == 'hdx_hxl_preview'),
            default_resource_view)

    return default_resource_view


def _check_resource(resource):
    shape_info = dataset_view_logic.has_shape_info(resource)
    if shape_info:
        return shape_info
    hxl_preview = _has_hxl_views(resource)
    if hxl_preview:
        return hxl_preview
    return None


def _has_hxl_views(resource):
    for view in resource.get("resource_views"):
        if view.get("view_type") == 'hdx_hxl_preview':
            return {
                'type': 'hdx_hxl_preview',
                "view_url": h.url_for("resource_view", id=view.get('package_id'),
                                      resource_id=view.get('resource_id'), view_id=view.get('id')),
                "view": view,
                "resource": resource
            }
    return None


def delete(id):
    """
    Delete package, HDX changed the redirection point
    """
    if 'cancel' in request.params:
        h.redirect_to(controller='package', action='edit', id=id)

    context = {'model': model, 'session': model.Session,
               'user': g.user or g.author, 'auth_user_obj': g.userobj}

    try:
        check_access('package_delete', context, {'id': id})
    except NotAuthorized:
        return abort(403, _('Unauthorized to delete package %s') % '')

    try:
        if request.method == 'POST':
            get_action('hdx_dataset_purge')(context, {'id': id})  # Create new action to fully delete
            h.flash_notice(_('Dataset has been deleted.'))
            return h.redirect_to('dashboard.datasets')
        pkg_dict = get_action('package_show')(context, {'id': id})
        # dataset_type = pkg_dict['type'] or 'dataset'
    except NotAuthorized:
        return abort(403, _('Unauthorized to delete package %s') % '')
    except NotFound:
        return abort(404, _('Dataset not found'))
    return render('package/confirm_delete.html', {'pkg_dict': pkg_dict})


hdx_search.add_url_rule(u'', view_func=search)
hdx_dataset.add_url_rule(u'', view_func=search)
hdx_dataset.add_url_rule(u'<id>', view_func=read)
hdx_dataset.add_url_rule(u'/delete/<id>', view_func=delete, methods=[u'GET', u'POST'])
hdx_dataset.add_url_rule(u'<id>/resource/<resource_id>/qa_sdcmicro_log', view_func=qa_sdcmicro_log)
hdx_dataset.add_url_rule(u'<id>/resource/<resource_id>/qa_pii_log/<file_name>', view_func=qa_pii_log)
