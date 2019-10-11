from flask import Blueprint

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckan.common import g

import ckanext.hdx_package.helpers.analytics as analytics
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed

get_action = tk.get_action
render = tk.render

hdx_light_dataset = Blueprint(u'hdx_light_dataset', __name__, url_prefix=u'/m/dataset')


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

    template_data = {
        'dataset_dict': dataset_dict,
        'analytics': analytics_dict
    }

    return render(u'light/dataset/read.html', template_data)


def _compute_analytics(dataset_dict):
    result = {}
    result['is_cod'] = analytics.is_cod(dataset_dict)
    result['is_indicator'] = analytics.is_indicator(dataset_dict)
    result['analytics_group_names'], result['analytics_group_ids'] = analytics.extract_locations_in_json(dataset_dict)
    result['analytics_dataset_availability'] = analytics.dataset_availability(dataset_dict)
    return result


hdx_light_dataset.add_url_rule(u'/<id>', view_func=read)
