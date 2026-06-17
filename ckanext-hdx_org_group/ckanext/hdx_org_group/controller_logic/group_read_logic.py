import unicodedata

import ckan.model as model
import ckan.plugins.toolkit as tk

import ckanext.hdx_org_group.helpers.country_helper as grp_h
import ckanext.hdx_org_group.helpers.caching as caching

from ckanext.hdx_org_group.controller_logic.group_search_logic import GroupSearchLogic

get_action = tk.get_action
NotFound = tk.ObjectNotFound
abort = tk.abort
_ = tk._

class LightGroupReadLogic(object):

    def __init__(self, group_id):
        self.id = group_id
        self.redirect_result = None
        self.country_dict = None
        self.widgets_data = None
        self.flask_route_name = 'hdx_light_group.light_read'

    def read(self):
        self.country_dict = self._fetch_group_info_and_datasets()
        if self.country_dict:
            self.widgets_data = self._fetch_widgets_data(self.country_dict)

        return self

    def _fetch_group_info_and_datasets(self):
        country_dict = grp_h.get_country(self.id)
        country_code = country_dict.get('name', self.id)
        try:
            search_logic = GroupSearchLogic(country_code, self.flask_route_name).search().init_archived_url_helper()
        except NotFound as e:
            abort(404, _('Page not found'))
        redirect_result = search_logic.redirect_if_needed()
        if redirect_result:
            self.redirect_result = redirect_result
            return None

        country_dict['template_data'] = search_logic.template_data
        return country_dict

    def _fetch_widgets_data(self, country_dict):
        not_filtered_facet_info = grp_h.get_not_filtered_facet_info(country_dict)
        data_dict = grp_h.get_template_data(country_dict, not_filtered_facet_info)
        return data_dict


class GroupReadLogic(LightGroupReadLogic):

    def __init__(self, group_id):
        super(GroupReadLogic, self).__init__(group_id)
        self.flask_route_name = 'hdx_group.read'

#
# class CountryToplineReadLogic(object):
#
#     def __init__(self, country_id):
#         super(CountryToplineReadLogic, self).__init__()
#         self.id = country_id
#         self.template_data = None
#
#     def read(self):
#         country_dict = grp_h.get_country(self.id)
#         top_line_data_list = caching.cached_topline_numbers(self.id)
#         self.template_data = {
#             'data': {
#                 'country_dict': country_dict,
#                 'widgets': {
#                     'top_line_data_list': top_line_data_list
#                 }
#             }
#         }
#         return self


class GroupIndexReadLogic(object):
    def __init__(self, user):
        self.user = user
        self.all_countries_world_1st = None
        self.total_count = 0
        self.hrp_count = 0
        self.grouped_countries = {}
        self.letters_present = []

    def read(self):
        context = {
            'model': model, 'session': model.Session,
            'user': self.user, 'for_view': True,
        }
        dataset_count_dict = self._fetch_dataset_counts(context, 'dataset')

        all_countries_world_1st = get_all_countries_world_first()
        for country in all_countries_world_1st:
            code = country['name']
            country['dataset_count'] = dataset_count_dict.get(code, 0)
            country['is_hrp'] = country.get('activity_level') == 'active'

        self.all_countries_world_1st = all_countries_world_1st

        non_world = [c for c in all_countries_world_1st if c['name'] != 'world']
        self.total_count = len(non_world)
        self.hrp_count = sum(1 for c in non_world if c.get('activity_level') == 'active')
        self.datagrid_count = sum(1 for c in non_world if c.get('data_completeness') == 'active')
        self.grouped_countries = self._group_by_letter(non_world)
        self.letters_present = sorted(self.grouped_countries.keys())

        return self

    def _group_by_letter(self, countries):
        grouped = {}
        for country in countries:
            display_name = country.get('display_name') or country.get('title', '')
            nfd = unicodedata.normalize('NFD', display_name)
            letter = ''
            for ch in nfd:
                if unicodedata.category(ch).startswith('L'):
                    letter = ch.upper()
                    break
            if letter and 'A' <= letter <= 'Z':
                grouped.setdefault(letter, []).append(country)
        return grouped

    def _fetch_dataset_counts(self, context, package_type):
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


def get_all_countries_world_first():
    all_countries = get_action('cached_group_list')()
    all_countries_world_1st = []
    for country in all_countries:
        code = country['name']
        if code == 'world':
            all_countries_world_1st.insert(0, country)
        else:
            all_countries_world_1st.append(country)

    return all_countries_world_1st
