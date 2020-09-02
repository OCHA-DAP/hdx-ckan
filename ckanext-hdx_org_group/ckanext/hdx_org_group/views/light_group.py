import json
import logging
import ckan
from flask import Blueprint

import ckan.common as common
import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_search.helpers.solr_query_helper as solr_query_helper
import ckanext.hdx_org_group.helpers.country_helper as grp_h
from ckanext.hdx_org_group.helpers.eaa_constants import EAA_FACET_NAMING_TO_INFO
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed, switch_url_path
from ckanext.hdx_org_group.controller_logic.group_search_logic import GroupSearchLogic



lookup_group_plugin = ckan.lib.plugins.lookup_group_plugin

g = common.g
request = common.request
render = tk.render
redirect = tk.redirect_to
get_action = tk.get_action
NotFound = tk.ObjectNotFound
check_access = tk.check_access
NotAuthorized = tk.NotAuthorized
abort = tk.abort
_ = tk._

log = logging.getLogger(__name__)

GROUP_TYPES = ['group']

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


# def light_read(id):
#     new_url = switch_url_path(None, False)
#     return redirect(new_url)

@check_redirect_needed
def light_read(id):
    return _read('light/group/read.html', id, True, False)


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

    package_type = 'dataset'
    ignore_capacity_check = False
    country_dict = grp_h.get_country(id)
    country_code = country_dict.get('name', id)
    search_logic = GroupSearchLogic(id=country_code)
    fq = 'groups:"{}"'.format(country_code)
    search_logic._search(package_type, additional_fq=fq, ignore_capacity_check=ignore_capacity_check)

    # non_filtered_facet_info = search_logic._prepare_facets_info(query_result.get('search_facets'), {}, {},
    #                                                     facets, query_result.get('count'), u'')
    #
    # non_filtered_facet_info['results'] = query_result.get('results', [])
    country_dict['template_data'] = search_logic.template_data
    not_filtered_facet_info = grp_h.get_not_filtered_facet_info(country_dict)
    template_data = grp_h.get_template_data(country_dict, not_filtered_facet_info)
    template_data = {
        'grp_dict': country_dict,
        'page_has_desktop_version': show_switch_to_desktop,
        'page_has_mobile_version': show_switch_to_mobile,
        'widgets_data': template_data
    }
    return render(template_file, template_data)


hdx_group.add_url_rule(u'', view_func=index)
hdx_group_eaa_maps.add_url_rule(u'', view_func=group_eaa_worldmap)
hdx_light_group.add_url_rule(u'', view_func=light_index)
hdx_light_group.add_url_rule(u'/<id>', view_func=light_read)


# def _get_country(id):
#     context = {'model': model, 'session': model.Session,
#                'user': g.user,
#                'schema': _db_to_form_schema(group_type='group'),
#                'for_view': True}
#     data_dict = {'id': id}
#
#     try:
#         context['include_datasets'] = False
#         group_dict = get_action('hdx_light_group_show')(context, data_dict)
#         if group_dict.get('type') not in GROUP_TYPES:
#             abort(404, _('Incorrect group type'))
#         return group_dict
#     except NotFound:
#         abort(404, _('Group not found'))
#     except NotAuthorized:
#         abort(403, _('Unauthorized to read group %s') % id)
#
#
# def _db_to_form_schema(group_type=None):
#     '''This is an interface to manipulate data from the database
#     into a format suitable for the form (optional)'''
#     return lookup_group_plugin(group_type).db_to_form_schema()
