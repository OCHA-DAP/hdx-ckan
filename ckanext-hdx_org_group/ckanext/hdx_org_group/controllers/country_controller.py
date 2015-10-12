'''
Created on Jan 13, 2015

@author: alexandru-m-g
'''
import json
import collections

import logging
import datetime as dt

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.common as common
import ckan.controllers.group as group
import ckan.lib.helpers as h

import ckanext.hdx_search.controllers.simple_search_controller as simple_search_controller
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
import ckanext.hdx_org_group.dao.indicator_access as indicator_access

render = base.render
abort = base.abort
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
c = common.c
request = common.request
_ = common._

log = logging.getLogger(__name__)
OrderedDict = collections.OrderedDict

group_type = 'group'

indicators_4_charts_list = [
    ('PVH140', 'mdgs'),
    ('PVN010', 'fao-foodsec'),
    ('PVW010', 'mdgs'),
    ('PVF020', 'faostat3'),
    ('PSE160', 'data.undp.org'),
    ('PCX051', 'mdgs'),
    ('PVE130', 'mdgs'),
    ('PCX060', 'mdgs'),
    ('RW002', 'RW'),
    ('PVE110', 'data.undp.org'),
    ('PVN050', 'mdgs'),
    ('PVN070', 'mdgs'),
    ('PVW040', 'mdgs')
]

indicators_4_charts = [el[0] for el in indicators_4_charts_list]

indicators_4_top_line_list = [
    ('PSP120', 'world-bank'),
    ('PSP090', 'world-bank'),
    ('PSE220', 'data.undp.org'),
    ('PSE030', 'world-bank'),
    ('CG300', 'world-bank')
]
indicators_4_top_line = [el[0] for el in indicators_4_top_line_list]


class CountryController(group.GroupController, simple_search_controller.HDXSimpleSearchController):
    def country_read(self, id):

        self.get_country(id)

        # country_uuid = c.group_dict.get('id', id)
        country_code = c.group_dict.get('name', id)

        self.get_dataset_results(country_code)
        # c.hdx_group_activities = self.get_activity_stream(country_uuid)

        (query, all_results) = self.get_dataset_search_results(country_code)
        vocab_topics_dict = all_results.get(
            'facets', {}).get('vocab_Topics', {})
        c.cont_browsing = self.get_cont_browsing(
            c.group_dict, vocab_topics_dict)

        c.show_overview = len(c.top_line_data_list) > 0 or len(c.chart_data_list) > 0

        result = render('country/country.html')

        return result

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
            c.group_dict = self._action(
                'hdx_light_group_show')(context, data_dict)
            # c.group = context['group']

        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read group %s') % id)

    def get_dataset_results(self, country_id):

        top_line_dao = indicator_access.IndicatorAccess(
            country_id, indicators_4_top_line_list, {'periodType': 'LATEST_YEAR_BY_COUNTRY'})

        top_line_results = top_line_dao.fetch_indicator_data_from_cps()
        top_line_data = top_line_results.get('results', [])

        if not top_line_data:
            log.warn(
                'No top line numbers found for country: {}'.format(country_id))
            top_line_data = []
        sorted_top_line_data = sorted(top_line_data,
                                      key=lambda x: indicators_4_top_line.index(x['indicatorTypeCode']))
        for el in sorted_top_line_data:
            el['formatted_value'] = formatters.format_decimal_number(
                el['value'], 2)

        c.top_line_data_list = sorted_top_line_data

        top_line_ind_codes = [el['indicatorTypeCode']
                              for el in sorted_top_line_data]

        chart_dao = indicator_access.IndicatorAccess(
            country_id, indicators_4_charts_list, {'sorting': 'INDICATOR_TYPE_ASC'})

        chart_dao.fetch_indicator_data_from_cps()
        chart_dataseries_dict = chart_dao.get_structured_data_from_cps()
        if not chart_dataseries_dict:
            log.warn('No chart data found for country: {}'.format(country_id))
            chart_dataseries_dict = {}

        # We can do the steps below because, in this case,
        # we know that each indicator type has only one source
        chart_data_dict = {}
        for key, value in chart_dataseries_dict.iteritems():
            try:
                # we're taking the first (and only) soruce
                new_value = value.itervalues().next()
                chart_data_dict[key] = new_value
            except Exception, e:
                log.warning("Exception while iterating dataseries data: " + e)


        # for code in chart_data_dict.keys():
        #     chart_data_dict[code] = sorted(chart_data_dict[code], key=lambda x: x.get('datetime', None))

        chart_data_list = []
        for code in indicators_4_charts:
            if code in chart_data_dict and len(chart_data_list) < 5:
                chart_data_list.append(chart_data_dict[code])

        chart_ind_codes = [chart['code'] for chart in chart_data_list]
        shown_dataseries_codes = [(el, '') for el in top_line_ind_codes + chart_ind_codes]
        shown_dataseries_dao = indicator_access.IndicatorAccess(country_id, shown_dataseries_codes)

        indic_extra_dict = shown_dataseries_dao.fetch_indicator_data_from_ckan()

        for chart in chart_data_list:
            code = chart['code']
            chart_extra = indic_extra_dict.get(code, None)
            chart['data'] = json.dumps(chart['data'])
            if chart_extra:
                chart['datasetLink'] = chart_extra.get('datasetLink')
                chart['datasetUpdateDate'] = chart_extra.get(
                    'datasetUpdateDate')

        c.chart_data_list = chart_data_list

        # updating the top line info with links and dates
        for el in sorted_top_line_data:
            cps_time = el.get('time', '')
            if cps_time:
                el['datasetUpdateDate'] = \
                    dt.datetime.strptime(cps_time, '%Y-%m-%d').strftime('%b %d, %Y')

            top_line_extra = indic_extra_dict.get(
                el['indicatorTypeCode'], None)
            if top_line_extra:
                el['datasetLink'] = top_line_extra.get('datasetLink')
                # el['datasetUpdateDate'] = top_line_extra.get(
                #     'datasetUpdateDate')

    # def get_activity_stream(self, country_uuid):
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user or c.author,
    #                'for_view': True}
    #     act_data_dict = {
    #         'id': country_uuid, 'group_uuid': country_uuid, 'limit': 7}
    #     result = get_action(
    #         'hdx_get_group_activity_list')(context, act_data_dict)
    #     return result

    def get_cont_browsing(self, group_dict, vocab_topics_dict):
        cont_browsing_dict = {
            'websites': self._process_websites(group_dict),
            'followers': self._get_followers(group_dict['id']),
            'topics': self._get_topics(vocab_topics_dict)

        }
        return cont_browsing_dict

    def _process_websites(self, group_dict):
        site_list = []
        if 'extras' in group_dict:
            extras_dict = {el['key']: el['value']
                           for el in group_dict['extras'] if el['state'] == u'active'}

            if 'relief_web_url' in extras_dict:
                site_list.append(
                    {'name': _('ReliefWeb'), 'url': extras_dict['relief_web_url']})
            site_list.append({'name': _('UNOCHA'), 'url': 'http://unocha.org'})
            if 'hr_info_url' in extras_dict:
                site_list.append(
                    {'name': _('HumanitarianResponse'), 'url': extras_dict['hr_info_url']})
            site_list.append(
                {'name': _('OCHA Financial Tracking Service'),
                 'url': 'http://fts.unocha.org/'}
            )

        return site_list

    def _get_followers(self, country_id):
        followers = get_action('group_follower_list')(
            {'ignore_auth': True}, {'id': country_id})
        followers_list = [
            {
                'name': f['display_name'],
                'url': h.url_for(controller='user', action='read', id=f['name'])
            } for f in followers
            ]

        return followers_list

    def _get_topics(self, vocab_topics_dict):
        topics_by_freq = OrderedDict(
            sorted(vocab_topics_dict.items(), key=lambda x: x[1]))
        topic_list = [
            {
                'name': topic,
                'url': h.url_for(controller='package', action='search', vocab_Topics=topic)
            } for topic in topics_by_freq.keys()
            ]

        return topic_list

    def get_dataset_search_results(self, country_code):
        fq = u'groups:"{}" +dataset_type:dataset'.format(country_code)
        facets = ['vocab_Topics']
        suffix = '#datasets-section'

        search_extras = {}
        ext_indicator = request.params.get('ext_indicator', '0')
        # if ext_indicator:
        search_extras['ext_indicator'] = ext_indicator

        # limit = self._allowed_num_of_items(search_extras)
        limit = 8
        page = self._page_number()
        params_nopage = {
            k: v for k, v in request.params.items() if k != 'page'}

        sort_by = request.params.get('sort', None)

        def pager_url(q=None, page=None):
            params = params_nopage
            params['page'] = page
            return h.url_for('country_read', id=country_code, **params) + suffix

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'for_view': True,
                   'auth_user_obj': c.userobj}

        self._set_other_links(
            suffix=suffix, other_params_dict={'id': country_code})
        (query, all_results) = self._performing_search('', fq, facets, limit, page, sort_by,
                                                       search_extras, pager_url, context)

        return query, all_results

    def _set_other_links(self, suffix='', other_params_dict=None):
        super(CountryController, self)._set_other_links(
            suffix=suffix, other_params_dict=other_params_dict)
        # c.other_links['advanced_search'] = h.url_for(
        #     'search', groups=other_params_dict['id'])

    def _get_named_route(self):
        return 'country_read'
