'''
Created on Jan 13, 2015

@author: alexandru-m-g
'''
import collections
import json
import logging

import ckan.common as common
import ckan.controllers.group as group
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.model as model
import ckan.lib.helpers as helpers
from ckan.controllers.api import CONTENT_TYPES

from operator import itemgetter

import ckanext.hdx_search.controllers.search_controller as search_controller
import ckanext.hdx_org_group.dao.widget_data_service as widget_data_service

render = base.render
abort = base.abort
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
c = common.c
request = common.request
_ = common._
response = common.response

log = logging.getLogger(__name__)
OrderedDict = collections.OrderedDict

group_type = 'group'


class CountryController(group.GroupController, search_controller.HDXSearchController):
    def country_read(self, id):
        country_dict = self.get_country(id)

        country_code = country_dict.get('name', id)

        if self._is_facet_only_request():
            c.full_facet_info = self.get_dataset_search_results(country_code)
            c.full_facet_info.get('facets', {}).pop('vocab_Topics', {})
            response.headers['Content-Type'] = CONTENT_TYPES['json']
            return json.dumps(c.full_facet_info)
        else:
            # self.get_dataset_results(country_code)
            # c.hdx_group_activities = self.get_activity_stream(country_uuid)

            not_filtered_facet_info = self._get_not_filtered_facet_info(country_dict)

            c.full_facet_info = self.get_dataset_search_results(country_code)
            vocab_topics_list = c.full_facet_info.get(
                'facets', {}).pop('vocab_Topics', {}).get('items', [])

            # Removed for now as per HDX-4927
            # c.cont_browsing = self.get_cont_browsing(
            #    c.group_dict, vocab_topics_list)

            template_data = self.get_template_data(country_dict, not_filtered_facet_info)

            result = render('country/country.html', extra_vars=template_data)

            return result

    def get_template_data(self, country_dict, not_filtered_facet_info):

        follower_count = get_action('group_follower_count')(
            {'model': model, 'session': model.Session},
            {'id': country_dict['id']}
        )

        top_line_data_list, chart_data_list = widget_data_service.build_widget_data_access(
            country_dict).get_dataset_results()

        organization_list = self._get_org_list_for_menu_from_facets(not_filtered_facet_info)
        f_thumbnail_list = self._get_thumbnail_list_for_featured()
        f_event_list = self._get_event_list_for_featured(country_dict['id'])
        f_organization_list = self._get_org_list_for_featured_from_facets(not_filtered_facet_info)
        f_tag_list = self._get_tag_list_for_featured_from_facets(not_filtered_facet_info)

        template_data = {
            'data': {
                'country_dict': country_dict,
                'stats_section': {
                    'organization_list': organization_list,
                    'num_of_organizations':
                        len(not_filtered_facet_info.get('facets', {}).get('organization', {}).get('items', [])),
                    'num_of_cods': not_filtered_facet_info.get('num_of_cods', 0),
                    'num_of_datasets': not_filtered_facet_info.get('num_of_total_items'),
                    'num_of_followers': follower_count
                },
                'widgets': {
                    'top_line_data_list': top_line_data_list,
                    'chart_data_list': chart_data_list,
                    'show': len(top_line_data_list) > 0 or len(chart_data_list) > 0
                },
                'featured_section': {
                    'thumbnail_list': f_thumbnail_list,
                    'event_list': f_event_list,
                    'organization_list': f_organization_list[:5],
                    'tag_list': f_tag_list[:10],
                    'show': len(f_organization_list) > 0 or len(f_tag_list) > 0
                },

            },
            'errors': None,
            'error_summary': '',
        }

        return template_data

    def _get_not_filtered_facet_info(self, country_dict):
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        fq = 'groups:"{}" +dataset_type:dataset'.format(country_dict.get('name'))
        query_result = self._performing_search(u'', fq, ['organization', 'tags'], 1, 1, 'total_res_downloads', None,
                                               None, context)
        non_filtered_facet_info = self._prepare_facets_info(query_result.get('search_facets'), {}, {},
                                                            {'tags': 'tags', 'organization': 'organization'},
                                                            query_result.get('count'), u'')

        return non_filtered_facet_info

    def _get_org_list_for_menu_from_facets(self, full_facet_info):
        org_list = [
            {
                'display_name': org.get('display_name'),
                'name': org.get('name'),
                'url': helpers.url_for('organization_read', id=org.get('name'))
            }
            for org in full_facet_info.get('facets', {}).get('organization', {}).get('items', [])
            ]
        return org_list

    def _get_org_list_for_featured_from_facets(self, full_facet_info):
        org_list = [
            {
                'display_name': org.get('display_name'),
                'name': org.get('name'),
                'url': helpers.url_for('organization_read', id=org.get('name'))
            }
            for org in full_facet_info.get('facets', {}).get('organization', {}).get('items', []) if
            org.get('name') != 'hdx'
            ]
        return org_list

    def _get_tag_list_for_featured_from_facets(self, full_facet_info):
        tag_list = [
            {
                'display_name': tag.get('display_name'),
                'count': tag.get('count'),
                'name': tag.get('name'),
                'url': helpers.url_for('package_search', tags=tag.get('name'))
            }
            for tag in full_facet_info.get('facets', {}).get('tags', {}).get('items', [])
            ]
        tag_list_by_count = sorted(tag_list, key=itemgetter('count'), reverse=True)
        return tag_list_by_count

    def _get_thumbnail_list_for_featured(self):
        thumbnail_list = [
            {
                'display_name': 'First Item Display Name',
                'type': 'Map Explorer|Event|Dataset',
                'url': '#',
                'thumbnail_url': '#'
            },
            {
                'display_name': 'Second Item Display Name',
                'type': 'COD',
                'url': '#',
                'thumbnail_url': '#'
            }

        ]
        return thumbnail_list

    def _get_event_list_for_featured(self, group_id):
        context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
        pages_list = get_action('group_page_list')(context, {'id': group_id})
        return pages_list

    def get_country(self, id):
        if group_type != self.group_type:
            abort(404, _('Incorrect group type'))

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True}
        data_dict = {'id': id}

        try:
            context['include_datasets'] = False
            group_dict = self._action(
                'hdx_light_group_show')(context, data_dict)

            return group_dict

        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read group %s') % id)

    # def get_activity_stream(self, country_uuid):
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user or c.author,
    #                'for_view': True}
    #     act_data_dict = {
    #         'id': country_uuid, 'group_uuid': country_uuid, 'limit': 7}
    #     result = get_action(
    #         'hdx_get_group_activity_list')(context, act_data_dict)
    #     return result

    # Removed for now as per HDX-4927
    # def get_cont_browsing(self, group_dict, vocab_topics_list):
    #     cont_browsing_dict = {
    #         'websites': self._process_websites(group_dict),
    #         'followers': self._get_followers(group_dict['id']),
    #         'topics': self._get_topics(vocab_topics_list)
    #
    #     }
    #     return cont_browsing_dict
    #
    # def _process_websites(self, group_dict):
    #     site_list = []
    #     if 'extras' in group_dict:
    #         extras_dict = {el['key']: el['value']
    #                        for el in group_dict['extras'] if el['state'] == u'active'}
    #
    #         if 'relief_web_url' in extras_dict:
    #             site_list.append(
    #                 {'name': _('ReliefWeb'), 'url': extras_dict['relief_web_url']})
    #         site_list.append({'name': _('UNOCHA'), 'url': 'http://unocha.org'})
    #         if 'hr_info_url' in extras_dict:
    #             site_list.append(
    #                 {'name': _('HumanitarianResponse'), 'url': extras_dict['hr_info_url']})
    #         site_list.append(
    #             {'name': _('OCHA Financial Tracking Service'),
    #              'url': 'http://fts.unocha.org/'}
    #         )
    #
    #     return site_list
    #
    # def _get_followers(self, country_id):
    #     followers = get_action('group_follower_list')(
    #         {'ignore_auth': True}, {'id': country_id})
    #     followers_list = [
    #         {
    #             'name': f['display_name'],
    #             'url': h.url_for(controller='user', action='read', id=f['name'])
    #         } for f in followers
    #         ]
    #
    #     return followers_list
    #
    # def _get_topics(self, vocab_topics_list):
    #     topic_list = [
    #         {
    #             'name': topic.get('name', ''),
    #             'url': h.url_for(controller='package', action='search', vocab_Topics=topic.get('name')),
    #             'count': topic.get('count', 0)
    #         } for topic in vocab_topics_list
    #     ]
    #
    #     topic_list.sort(key=lambda x: x.get('count', 0), reverse=True)
    #
    #     return topic_list

    def get_dataset_search_results(self, country_code):
        package_type = 'dataset'

        suffix = '#datasets-section'

        params_nopage = {
            k: v for k, v in request.params.items() if k != 'page'}

        def pager_url(q=None, page=None):
            params = params_nopage
            params['page'] = page
            return h.url_for('country_read', id=country_code, **params) + suffix

        fq = 'groups:"{}"'.format(country_code)
        facets = {
            'vocab_Topics': _('Topics')
        }
        full_facet_info = self._search(package_type, pager_url, additional_fq=fq, additional_facets=facets)
        locations = full_facet_info.get('facets', {}).get('groups', {}).get('items', [])
        locations[:] = [loc for loc in locations if loc.get('name', '') != country_code]

        c.other_links['current_page_url'] = h.url_for('country_read', id=country_code)

        return full_facet_info
