from flask import Blueprint

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckan.common import g
import ckan.logic as logic

import ckanext.hdx_package.helpers.analytics as analytics
import ckanext.hdx_package.helpers.custom_pages as cp_h
from ckanext.hdx_search.controller_logic.search_logic import SearchLogic, ArchivedUrlHelper
from ckanext.hdx_theme.util.http_exception_helper import catch_http_exceptions
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed

get_action = tk.get_action
check_access = tk.check_access
render = tk.render
abort = tk.abort
_ = tk._

NotAuthorized = tk.NotAuthorized
NotFound = logic.NotFound

hdx_light_dataset = Blueprint(u'hdx_light_dataset', __name__, url_prefix=u'/m/dataset')
hdx_light_search = Blueprint(u'hdx_light_search', __name__, url_prefix=u'/m/search')


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

@check_redirect_needed
@catch_http_exceptions
def read(id):
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'auth_user_obj': g.userobj,
        u'for_view': True
    }
    data_dict = {
        u'id': id
    }

    dataset_dict = get_action('package_show')(context, data_dict)
    org_dict = dataset_dict.get('organization') or {}
    org_id = org_dict.get('id', None)
    org_info_dict = _get_org_extras(org_id)
    user_survey_url = org_info_dict.get('user_survey_url')
    if dataset_dict.get('type') == 'dataset':
        analytics_dict = _compute_analytics(dataset_dict)
        dataset_dict['page_list'] = cp_h.hdx_get_page_list_for_dataset(context, dataset_dict)
        dataset_dict['link_list'] = get_action('hdx_package_links_by_id_list')(context, {'id': dataset_dict.get('name')})

        template_data = {
            'dataset_dict': dataset_dict,
            'analytics': analytics_dict,
            'user_survey_url': user_survey_url
        }

        return render(u'light/dataset/read.html', template_data)
    else:
        raise NotFound


@check_redirect_needed
def search():
    return generic_search(u'light/search/search.html')


def generic_search(html_template):
    try:
        context = {'model': model, 'user': g.user,
                   'auth_user_obj': g.userobj}
        check_access('site_read', context)
    except NotAuthorized:
        abort(403, _('Not authorized to see this page'))

    search_logic = SearchLogic()

    search_logic._search(use_solr_collapse=True)

    archived_url_helper = search_logic.add_archived_url_helper()
    redirect_result = archived_url_helper.redirect_if_needed()
    if redirect_result:
        return redirect_result

    data_dict = {'data': search_logic.template_data}
    return render(html_template, data_dict)


def _compute_analytics(dataset_dict):
    result = {}
    result['is_cod'] = analytics.is_cod(dataset_dict)
    result['is_indicator'] = analytics.is_indicator(dataset_dict)
    result['is_archived'] = analytics.is_archived(dataset_dict)
    result['analytics_group_names'], result['analytics_group_ids'] = analytics.extract_locations_in_json(dataset_dict)
    result['analytics_dataset_availability'] = analytics.dataset_availability(dataset_dict)
    return result


hdx_light_search.add_url_rule(u'', view_func=search)
hdx_light_dataset.add_url_rule(u'', view_func=search)
hdx_light_dataset.add_url_rule(u'/<id>', view_func=read)
