'''
Created on Dec 22, 2014

@author: alexandru-m-g
'''
import json
import logging

import ckanext.hdx_org_group.helpers.organization_helper as helper

import ckan.common as common
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.model as model

c = common.c
request = common.request
get_action = logic.get_action
NotFound = logic.NotFound

log = logging.getLogger(__name__)


class BrowseController(base.BaseController):

    def index(self):
        user = c.user or c.author
        c.countries = json.dumps(self.get_countries(user))

        request_params = {
            'sort_option': request.params.get('sort', 'title asc'),
            'page': request.params.get('page', 1)
        }
        c.organizations, c.organization_count = \
            self.get_organizations(user, request_params)
        c.topics = self.get_topics()
        c.topic_icons = self.get_topic_icons()

        return base.render('browse/browse.html')

    def get_countries(self, user):

        context = {'model': model, 'session': model.Session,
                   'user': user, 'for_view': True,
                   }
        dataset_count_dict = self._get_dataset_counts(context)

        all_countries = get_action('cached_group_list')()

        all_countries_world_1st = []
        for country in all_countries:
            code = country['name']

            if code == 'world':
                all_countries_world_1st.insert(0, country)
            else:
                all_countries_world_1st.append(country)

            country['dataset_count'] = dataset_count_dict.get(code, None)

        return all_countries_world_1st

    def get_organizations(self, user, request_params):
        context = {'model': model, 'session': model.Session,
                   'user': user, 'for_view': True,
                }

        sort_option = request_params.get('sort_option', 'title asc')

        data_dict = {
            'all_fields': True,
            'sort': sort_option
        }

        all_orgs = get_action('organization_list')(context, data_dict)

        all_orgs = helper.filter_and_sort_results_case_insensitive(all_orgs, sort_option)

        def pager_url(q=None, page=None):
            if sort_option:
                url = h.url_for(
                    'browse_list', page=page, sort=sort_option) + \
                    '#organizationsSection'
            else:
                url = h.url_for('browse_list', page=page) + \
                    '#organizationsSection'
            return url

        page = h.Page(
            collection=all_orgs,
            page=request_params.get('page', 1),
            url=pager_url,
            items_per_page=20
        )

        return (page, len(all_orgs))

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

    def _get_dataset_counts(self, context):
        search = {
            'q': None,
            'fq': None,
            'facet.field': ['groups'],
            'facet.limit': 1000,
            'rows': 1,
        }
        result = get_action('package_search')(context, search)
        if 'facets' in result and 'groups' in result['facets']:
            return result['facets']['groups']
        else:
            return {}


    def get_topic_icons(self):

        #icons reference can be found in humanitarian_icons.css
        ret = {
            u'economy': {
                'icon': 'topic-icon-activity_financing',
                'title': 'Economy'
            },
            u'education': {
                'icon': 'topic-icon-cluster_education',
                'title': 'Education'
            },
            u'emergency telecommunications': {
                'icon': 'topic-icon-cluster_emergency_telecommunications',
                'title': 'Emergency Telecommunications'
            },
            u'food and nutrition': {
                'icon': 'topic-icon-cluster_food_security',
                'title': 'Food and Nutrition'
            },
            u'gender': {
                'icon': 'topics-icon-gender.png',
                'title': 'Gender'
            },
            u'health': {
                'icon': 'topic-icon-cluster_health',
                'title': 'Health'
            },
            u'humanitarian funding': {
                'icon': 'topic-icon-activity_fund',
                'title': 'Humanitarian Funding'
            },
            u'humanitarian profile': {
                'icon': 'topic-icon-activity_humanitarian_programme_cycle',
                'title': 'Humanitarian Profile'
            },
            u'logistics': {
                'icon': 'topic-icon-cluster_logistics',
                'title': 'Logistics'
            },
            u'population': {
                'icon': 'topic-icon-people_affected_population',
                'title': 'Population'
            },
            u'water sanitation and hygiene': {
                'icon': 'topic-icon-wash_sanitation',
                'title': 'Water Sanitation and Hygiene'
            }
        }
        return ret
