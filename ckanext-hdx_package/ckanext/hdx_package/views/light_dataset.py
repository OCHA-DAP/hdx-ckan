from flask import Blueprint

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckan.common import g

import ckanext.hdx_package.helpers.analytics as analytics
import ckanext.hdx_package.helpers.custom_pages as cp_h
from ckanext.hdx_search.controller_logic.search_logic import SearchLogic

from ckanext.hdx_theme.util.light_redirect import check_redirect_needed

get_action = tk.get_action
check_access = tk.check_access
render = tk.render
abort = tk.abort
_ = tk._

NotAuthorized = tk.NotAuthorized

hdx_light_dataset = Blueprint(u'hdx_light_dataset', __name__, url_prefix=u'/m/dataset')
hdx_light_search = Blueprint(u'hdx_light_search', __name__, url_prefix=u'/m/search')


@check_redirect_needed
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
    analytics_dict = _compute_analytics(dataset_dict)
    dataset_dict['page_list'] = cp_h.hdx_get_page_list_for_dataset(context, dataset_dict)
    dataset_dict['link_list'] = get_action('hdx_package_links_by_id_list')(context, {'id': dataset_dict.get('name')})

    template_data = {
        'dataset_dict': dataset_dict,
        'analytics': analytics_dict
    }

    return render(u'light/dataset/read.html', template_data)


@check_redirect_needed
def search():
    try:
        context = {'model': model, 'user': g.user,
                   'auth_user_obj': g.userobj}
        check_access('site_read', context)
    except NotAuthorized:
        abort(403, _('Not authorized to see this page'))

    package_type = 'dataset'

    search_logic = SearchLogic()

    search_logic._search(package_type, use_solr_collapse=True, hide_archived=True)

    data_dict = {'data': search_logic.template_data}
    return render(u'light/search/search.html', data_dict)


def _compute_analytics(dataset_dict):
    result = {}
    result['is_cod'] = analytics.is_cod(dataset_dict)
    result['is_indicator'] = analytics.is_indicator(dataset_dict)
    result['analytics_group_names'], result['analytics_group_ids'] = analytics.extract_locations_in_json(dataset_dict)
    result['analytics_dataset_availability'] = analytics.dataset_availability(dataset_dict)
    return result


hdx_light_search.add_url_rule(u'', view_func=search)
hdx_light_dataset.add_url_rule(u'', view_func=search)
hdx_light_dataset.add_url_rule(u'/<id>', view_func=read)
