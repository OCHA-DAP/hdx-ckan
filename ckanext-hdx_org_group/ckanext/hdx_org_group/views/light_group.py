import json
import logging

from flask import Blueprint

import ckan.common as common
import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_search.helpers.solr_query_helper as solr_query_helper
from ckanext.hdx_org_group.helpers.eaa_constants import EAA_FACET_NAMING_TO_INFO
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed, switch_url_path


g = common.g
request = common.request
render = tk.render
redirect = tk.redirect_to
get_action = tk.get_action
NotFound = tk.ObjectNotFound

log = logging.getLogger(__name__)


hdx_group = Blueprint(u'hdx_group', __name__, url_prefix=u'/group')
hdx_group_eaa_maps = Blueprint(u'hdx_group_eaa_maps', __name__, url_prefix=u'/eaa-worldmap')
hdx_light_group = Blueprint(u'hdx_light_group', __name__, url_prefix=u'/m/group')


def _get_all_countries_world_first():
    all_countries = get_action('cached_group_list')()
    all_countries_world_1st = []
    for country in all_countries:
        code = country['name']
        if code == 'world':
            all_countries_world_1st.insert(0, country)
        else:
            all_countries_world_1st.append(country)

    return all_countries_world_1st


def index():
    return _index('light/group/index.html', False, False)


def light_index():
    new_url = switch_url_path(None, False)
    return redirect(new_url)


def _index(template_file, show_switch_to_desktop, show_switch_to_mobile):
    user = g.user
    countries = json.dumps(get_countries(user))
    template_data = {
        'countries': countries,
        'page_has_desktop_version': show_switch_to_desktop,
        'page_has_mobile_version': show_switch_to_mobile,
    }
    return render(template_file, template_data)


def group_eaa_worldmap():
    countries = json.dumps(get_eaa_countries_data())
    template_data = {
        'countries': countries,
    }
    return render('group/eaa_worldmap.html', template_data)


def get_countries(user):
    context = {'model': model, 'session': model.Session,
               'user': user, 'for_view': True,
               }
    dataset_count_dict = _get_dataset_counts(context, 'dataset')
    indicator_count_dict = _get_dataset_counts(context, 'indicator')

    all_countries_world_1st = _get_all_countries_world_first()

    for country in all_countries_world_1st:
        code = country['name']
        country['dataset_count'] = dataset_count_dict.get(code, 0) + indicator_count_dict.get(code, 0)
        country['indicator_count'] = indicator_count_dict.get(code, None)

    return all_countries_world_1st


def get_eaa_countries_data():
    query_tag = 'eaa'
    search = {
        'q': None,
        'facet.limit': 1000,
        'fq': 'vocab_Topics:education',
        'facet.query': [
            solr_query_helper.generate_facet_query_from_list(k, query_tag, 'vocab_Topics', v.get('tag_list'),
                                                             negate=v.get('negate'))
            for k, v in EAA_FACET_NAMING_TO_INFO.items()],
        'facet.pivot': '{!query=' + query_tag + '}groups',
        'rows': 1,
    }
    result = get_action('package_search')({}, search)

    all_countries_world_1st = _get_all_countries_world_first()

    for country in all_countries_world_1st:
        code = country['name']

        eaa_stats = result.get('facet_pivot', {}).get('groups', {}).get(code)
        if eaa_stats:
            for key in eaa_stats.keys():
                facet_info = EAA_FACET_NAMING_TO_INFO.get(key)
                if facet_info:
                    url_dict = {
                        'groups': code,
                        facet_info.get('url_param_name'): True
                    }
                    eaa_stats[key]['url'] = h.url_for('search', **url_dict)
        country['eaa_stats'] = eaa_stats

    return all_countries_world_1st


def _get_dataset_counts(context, package_type):
    search = {
        'q': None,
        'fq': '+extras_indicator: 1' if package_type == 'indicator' else '-extras_indicator: 1',
        'facet.field': ['groups'],
        'facet.limit': 1000,
        'rows': 1,
    }
    result = get_action('package_search')(context, search)
    if 'facets' in result and 'groups' in result['facets']:
        return result['facets']['groups']
    else:
        return {}


def light_read(id):
    new_url = switch_url_path(None, False)
    return redirect(new_url)


hdx_group.add_url_rule(u'', view_func=index)
hdx_group_eaa_maps.add_url_rule(u'', view_func=group_eaa_worldmap)
hdx_light_group.add_url_rule(u'', view_func=light_index)
hdx_light_group.add_url_rule(u'/<id>', view_func=light_read)
