'''
Created on Jan 13, 2015

@author: alexandru-m-g
'''
import collections
import json
import logging
from operator import itemgetter

import ckanext.hdx_org_group.helpers.country_helper as country_helper
import ckanext.hdx_org_group.helpers.caching as caching
import ckanext.hdx_package.helpers.screenshot as screenshot
import ckanext.hdx_search.controllers.search_controller as search_controller

import ckan.common as common
import ckan.controllers.group as group
import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.helpers as helpers
import ckan.logic as logic
import ckan.model as model

from ckan.controllers.api import CONTENT_TYPES
from ckan.common import config

from ckanext.hdx_search.helpers.constants import DEFAULT_SORTING

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
    def country_read(self, id, get_only_toplines=False):
        # import cProfile
        # profile = cProfile.Profile()
        # profile.enable()
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
            latest_cod_dataset = country_helper.get_latest_cod_datatset(country_dict.get('name'))

            c.full_facet_info = self.get_dataset_search_results(country_code)

            # Removed for now as per HDX-4927
            # c.cont_browsing = self.get_cont_browsing(
            #    c.group_dict, vocab_topics_list)

            template_data = self.get_template_data(country_dict, not_filtered_facet_info, latest_cod_dataset)

            # data grid / data completeness code
            if country_dict.get('data_completeness') == 'active':
                pass

            if get_only_toplines:
                result = render('country/country_topline.html', extra_vars=template_data)
            else:
                result = render('country/country.html', extra_vars=template_data)
            # profile.disable()
            # profile.print_stats('cumulative')
            return result

    def country_topline(self, id):
        log.info("The id of the page is: " + id)

        country_dict = self.get_country(id)
        top_line_data_list = caching.cached_topline_numbers(id)
        template_data = {
            'data': {
                'country_dict': country_dict,
                'widgets': {
                    'top_line_data_list': top_line_data_list
                }
            }
        }
        return base.render('country/country_topline.html', extra_vars=template_data)

        # return self.country_read(id=id, get_only_toplines=True)

    def get_template_data(self, country_dict, not_filtered_facet_info, latest_cod_dataset):

        follower_count = get_action('group_follower_count')(
            {'model': model, 'session': model.Session},
            {'id': country_dict['id']}
        )

        top_line_data_list = caching.cached_topline_numbers(country_dict['id'], country_dict.get('activity_level'))

        organization_list = self._get_org_list_for_menu_from_facets(not_filtered_facet_info)
        f_event_list = self._get_event_list_for_featured(country_dict['id'])
        f_thumbnail_list = self._get_thumbnail_list_for_featured(country_dict, f_event_list,
                                                                 not_filtered_facet_info.get('results'),
                                                                 latest_cod_dataset)
        f_organization_list = self._get_org_list_for_featured_from_facets(not_filtered_facet_info)
        f_tag_list = self._get_tag_list_for_featured_from_facets(not_filtered_facet_info)

        data_completness = self._get_data_completeness(country_dict.get('name')) \
                            if country_dict.get('data_completeness') == 'active' else None

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
                    # 'chart_data_list': chart_data_list,
                    'show': len(top_line_data_list) > 0  # or len(chart_data_list) > 0
                },
                'featured_section': {
                    'thumbnail_list': f_thumbnail_list,
                    'event_list': f_event_list,
                    'organization_list': f_organization_list[:5],
                    'tag_list': f_tag_list[:10],
                    'show': len(f_organization_list) > 0 or len(f_tag_list) > 0
                },
                'data_completness': data_completness,

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
        query_result = self._performing_search(u'', fq, ['organization', 'tags'], 2, 1, DEFAULT_SORTING, None,
                                               None, context)
        non_filtered_facet_info = self._prepare_facets_info(query_result.get('search_facets'), {}, {},
                                                            {'tags': 'tags', 'organization': 'organization'},
                                                            query_result.get('count'), u'')

        non_filtered_facet_info['results'] = query_result.get('results', [])

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
                'count': org.get('count'),
                'url': helpers.url_for('organization_read', id=org.get('name'))
            }
            for org in full_facet_info.get('facets', {}).get('organization', {}).get('items', []) if
            org.get('name') != 'hdx'
            ]
        result = sorted(org_list, key=itemgetter('count'), reverse=True)
        return result

    def _get_tag_list_for_featured_from_facets(self, full_facet_info):
        tag_list = [
            {
                'display_name': tag.get('display_name'),
                'count': tag.get('count'),
                'name': tag.get('name'),
                'url': '?tags='+tag.get('name')+'#dataset-filter-start'
            }
            for tag in full_facet_info.get('facets', {}).get('tags', {}).get('items', [])
            ]
        tag_list_by_count = sorted(tag_list, key=itemgetter('count'), reverse=True)
        return tag_list_by_count

    def _get_thumbnail_list_for_featured(self, country_dict, event_list, latest_datasets, latest_cod_dataset):
        '''
        :param country_dict:
        :type country_dict: dict
        :param event_list: if this was already fetched in the controller we can reuse it
        :type event_list: list
        :param latest_datasets: a list of the latest updated datasets for the country
        :type latest_datasets: list
        :return: list of dicts containing display_name, type and url for the featured thumbnails
        :rtype: list
        '''

        cloned_latest_datasets = latest_datasets[:]
        default_thumbnail_url = '/images/featured_locs_placeholder1.png'
        thumbnail_list = [None, None]
        if event_list:
            thumbnail_list[0] = self.__event_as_thumbnail_dict(event_list[0], default_thumbnail_url)
        elif cloned_latest_datasets:
            thumbnail_list[0] = self.__dataset_as_thumbnail_dict(cloned_latest_datasets[0], default_thumbnail_url)
            del cloned_latest_datasets[0]
        if latest_cod_dataset:
            cod_thumbnail_url = screenshot.create_download_link(latest_cod_dataset, default_thumbnail_url)
            thumbnail_list[1] = self.__dataset_as_thumbnail_dict(latest_cod_dataset, cod_thumbnail_url, True)
        elif cloned_latest_datasets:
            thumbnail_list[1] = self.__dataset_as_thumbnail_dict(cloned_latest_datasets[0], default_thumbnail_url)
            del cloned_latest_datasets[0]

        if thumbnail_list[0] and thumbnail_list[1] \
                and thumbnail_list[0].get('url') == thumbnail_list[1].get('url') and cloned_latest_datasets:
            thumbnail_list[0] = self.__dataset_as_thumbnail_dict(cloned_latest_datasets[0], default_thumbnail_url)
            del cloned_latest_datasets[0]

        # thumbnail_list[0]['thumbnail_url'] = '/images/featured_locs_placeholder1.png'
        # thumbnail_list[1]['thumbnail_url'] = '/images/featured_locs_placeholder2.png'
        return thumbnail_list

    def __dataset_as_thumbnail_dict(self, dataset_dict, thumbnail_url, is_cod=False):
        return {
            'display_name': dataset_dict.get('title'),
            'type': 'COD' if is_cod else 'Dataset',
            'url': h.url_for('dataset_read', id=dataset_dict.get('name')),
            'thumbnail_url': thumbnail_url
        }

    def __event_as_thumbnail_dict(self, event_dict, thumbnail_url, is_cod=False):
        return {
            'display_name': event_dict.get('title'),
            'type': 'Event',
            'url': h.url_for('read_event', id=event_dict.get('name')),
            'thumbnail_url': thumbnail_url
        }

    def _get_event_list_for_featured(self, group_id):
        context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}
        pages_list = get_action('group_page_list')(context, {'id': group_id})
        return pages_list

    @staticmethod
    def _get_data_completeness(location_code):

        cached = config.get('hdx.datagrid.prod') == 'true'

        data = None
        if cached:
            data = caching.cached_data_completeness(location_code)
        else:
            data = caching.cached_data_completeness.original(location_code)

        return data


    def get_country(self, id):
        # group_type = self._ensure_controller_matches_group_type(
        #     id.split('@')[0])

        context = {'model': model, 'session': model.Session,
                   'user': c.user,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True}
        data_dict = {'id': id}

        try:
            context['include_datasets'] = False
            group_dict = self._action('hdx_light_group_show')(context, data_dict)
            if group_dict.get('type') not in self.group_types:
                abort(404, _('Incorrect group type'))
            return group_dict

        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            abort(403, _('Unauthorized to read group %s') % id)

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

        full_facet_info = self._search(package_type, pager_url, additional_fq=fq)
        locations = full_facet_info.get('facets', {}).get('groups', {}).get('items', [])
        locations[:] = [loc for loc in locations if loc.get('name', '') != country_code]

        c.other_links['current_page_url'] = h.url_for('country_read', id=country_code)

        return full_facet_info
