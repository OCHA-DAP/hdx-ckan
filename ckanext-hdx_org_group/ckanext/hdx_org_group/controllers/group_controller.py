'''
Created on Aug 11, 2015

@author: mbellotti
'''
import json
import logging

import ckan.common as common
import ckan.controllers.group as grp
import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.lib.helpers as h

import ckanext.hdx_search.helpers.solr_query_helper as solr_query_helper

from ckanext.hdx_org_group.helpers.eaa_constants import EAA_FACET_NAMING_TO_INFO

c = common.c
request = common.request
get_action = logic.get_action
NotFound = logic.NotFound

log = logging.getLogger(__name__)


class HDXGroupController(grp.GroupController):

    @staticmethod
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

    def index(self):
        user = c.user or c.author
        c.countries = json.dumps(self.get_countries(user))
        return base.render('group/index.html')

    def group_worldmap(self):
        user = c.user or c.author
        c.countries = json.dumps(self.get_countries(user))
        return base.render('group/worldmap.html')

    def group_eaa_worldmap(self):
        c.countries = json.dumps(self.get_eaa_countries_data())
        return base.render('group/eaa_worldmap.html')

    def get_countries(self, user):

        context = {'model': model, 'session': model.Session,
                   'user': user, 'for_view': True,
                   }
        dataset_count_dict = self._get_dataset_counts(context, 'dataset')
        indicator_count_dict = self._get_dataset_counts(context, 'indicator')

        all_countries_world_1st = self._get_all_countries_world_first()

        for country in all_countries_world_1st:
            code = country['name']
            country['dataset_count'] = dataset_count_dict.get(code, 0) + indicator_count_dict.get(code, 0)
            country['indicator_count'] = indicator_count_dict.get(code, None)

        return all_countries_world_1st

    def get_eaa_countries_data(self):
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

        all_countries_world_1st = self._get_all_countries_world_first()

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

    def _get_dataset_counts(self, context, package_type):
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
