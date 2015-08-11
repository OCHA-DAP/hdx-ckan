'''
Created on Aug 11, 2015

@author: mbellotti
'''
import json

import logging

import ckan.lib.base as base
import ckan.model as model
import ckan.common as common
import ckan.logic as logic
import ckan.lib.helpers as h

import ckanext.hdx_org_group.helpers.organization_helper as helper
import ckan.controllers.group as grp

c = common.c
request = common.request
get_action = logic.get_action
NotFound = logic.NotFound

log = logging.getLogger(__name__)


class HDXGroupController(grp.GroupController):

    def index(self):
        user = c.user or c.author
        c.countries = json.dumps(self.get_countries(user))
        return base.render('group/index.html')

    def get_countries(self, user):

        context = {'model': model, 'session': model.Session,
                   'user': user, 'for_view': True,
                   }
        dataset_count_dict = self._get_dataset_counts(context, 'dataset')
        indicator_count_dict = self._get_dataset_counts(context, 'indicator')

        all_countries = get_action('cached_group_list')()

        all_countries_world_1st = []
        for country in all_countries:
            code = country['name']

            if code == 'world':
                all_countries_world_1st.insert(0, country)
            else:
                all_countries_world_1st.append(country)

            country['dataset_count'] = dataset_count_dict.get(code, None)
            country['indicator_count'] = indicator_count_dict.get(code, None)

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
