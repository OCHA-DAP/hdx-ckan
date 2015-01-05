'''
Created on Dec 22, 2014

@author: alexandru-m-g
'''
import json

import logging

import ckan.lib.base as base
import ckan.model as model
import ckan.common as common
import ckan.logic as logic
import ckan.lib.helpers as h

c = common.c
request = common.request
get_action = logic.get_action
NotFound = logic.NotFound

log = logging.getLogger(__name__)


class BrowseController(base.BaseController):

    def index(self):
        c.countries = json.dumps(self.get_countries())
        c.organizations = self.get_organizations()
        c.topics = self.get_topics()

        return base.render('browse/browse.html')

    def get_countries(self):

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
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

    def get_organizations(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        sort_option = c.sort_by_selected = request.params.get(
            'sort', 'title asc')

        data_dict = {
            'all_fields': True,
            'sort': sort_option
        }

        all_orgs = get_action('organization_list')(context, data_dict)

        def pager_url(q=None, page=None):
            if sort_option:
                url = h.url_for(
                    'browse_list', page=page, sort=sort_option) + \
                    '#organizations-section'
            else:
                url = h.url_for('browse_list', page=page) + \
                    '#organizations-section'
            return url

        c.page = h.Page(
            collection=all_orgs,
            page=request.params.get('page', 1),
            url=pager_url,
            items_per_page=20
        )

        return all_orgs

    def get_topics(self):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}
        try:
            all_topics = get_action('tag_list')(
                context, {'vocabulary_id': 'Topics'})
        except NotFound, e:
            all_topics = []
            log.error('ERROR getting vocabulary named Topics: %r' %
                      str(e.extra_msg))
        return all_topics

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
