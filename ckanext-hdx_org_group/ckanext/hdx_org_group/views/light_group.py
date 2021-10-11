import json
import logging
import ckan
from flask import Blueprint

import ckan.common as common
import ckan.lib.helpers as h
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_search.helpers.solr_query_helper as solr_query_helper
from ckanext.hdx_org_group.controller_logic.group_read_logic import LightGroupReadLogic, get_all_countries_world_first
from ckanext.hdx_org_group.helpers.eaa_constants import EAA_FACET_NAMING_TO_INFO
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed, switch_url_path


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

hdx_group_eaa_maps = Blueprint(u'hdx_group_eaa_maps', __name__, url_prefix=u'/eaa-worldmap')
hdx_light_group = Blueprint(u'hdx_light_group', __name__, url_prefix=u'/m/group')


def light_index():
    new_url = switch_url_path(None, False)
    return redirect(new_url)


def group_eaa_worldmap():
    countries = json.dumps(get_eaa_countries_data())
    template_data = {
        'countries': countries,
    }
    return render('group/eaa_worldmap.html', template_data)


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

    all_countries_world_1st = get_all_countries_world_first()

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

    group_read_logic = LightGroupReadLogic(group_id=id)
    group_read_logic.read()
    if group_read_logic.redirect_result:
        return group_read_logic.redirect_result
    else:
        template_data = {
            'grp_dict': group_read_logic.country_dict,
            'page_has_desktop_version': show_switch_to_desktop,
            'page_has_mobile_version': show_switch_to_mobile,
            'widgets_data': group_read_logic.widgets_data
        }
        return render(template_file, template_data)


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
