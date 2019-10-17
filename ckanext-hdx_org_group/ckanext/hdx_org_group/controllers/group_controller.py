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

import ckanext.hdx_search.helpers.solr_query_helper as solr_query_helper

from ckanext.hdx_org_group.helpers.constants \
    import EAA_CRISIS_RESPONSE, EAA_EDUCATION_FACILITIES, EAA_EDUCATION_STATISTICS, EAA_ALL_USED_TAGS

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
                solr_query_helper.generate_facet_query_from_list('education_statistics', query_tag, 'vocab_Topics',
                                                                 EAA_EDUCATION_STATISTICS),
                solr_query_helper.generate_facet_query_from_list('education_facilities', query_tag, 'vocab_Topics',
                                                                 EAA_EDUCATION_FACILITIES),
                solr_query_helper.generate_facet_query_from_list('crisis_response', query_tag, 'vocab_Topics',
                                                                 EAA_CRISIS_RESPONSE),
                solr_query_helper.generate_facet_query_from_list('other', query_tag, 'vocab_Topics',
                                                                 EAA_ALL_USED_TAGS, negate=True),
            ],
            'facet.pivot': '{!query=' + query_tag + '}groups',
            'rows': 1,
        }
        result = get_action('package_search')({}, search)

        all_countries_world_1st = self._get_all_countries_world_first()

        for country in all_countries_world_1st:
            code = country['name']
            country['eaa_stats'] = result.get('facet_pivot', {}).get('groups', {}).get(code)

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
