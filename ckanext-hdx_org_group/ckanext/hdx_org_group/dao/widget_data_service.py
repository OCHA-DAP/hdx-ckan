import logging
import json
import datetime as dt

import pylons.config as config

import ckanext.hdx_org_group.dao.indicator_access as indicator_access
import ckanext.hdx_org_group.dao.rw_access as rw_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters

log = logging.getLogger(__name__)

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


def build_widget_data_access(country_dict):
    '''

    :param country_dict:
    :type country_dict: dict
    :return: instance of class WidgetDataAccess or its subclasses
    :rtype: WidgetDataService
    '''
    if country_dict.get('activity_level') == 'active':
        return RWWidgetDataService(country_dict.get('name'))
    else:
        return WidgetDataService(country_dict.get('name'))

class WidgetDataService(object):

    def __init__(self, country_name):
        self.country_name = country_name


    def get_dataset_results(self):

        country_id = self.country_name

        top_line_dao = indicator_access.IndicatorAccess(
            country_id, indicators_4_top_line_list, {'periodType': 'LATEST_YEAR_BY_COUNTRY'}, recompute_units=True)

        top_line_results = top_line_dao.fetch_indicator_data_from_cps()
        top_line_data = top_line_results.get('results', [])

        if not top_line_data:
            log.warn(
                'No top line numbers found for country: {}'.format(country_id))
            top_line_data = []
        sorted_top_line_data = sorted(top_line_data,
                                      key=lambda x: indicators_4_top_line.index(x['indicatorTypeCode']))

        formatters.TopLineItemsWithDateFormatter(top_line_data).format_results()


        # c.top_line_data_list = sorted_top_line_data

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

        # c.chart_data_list = chart_data_list

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

        return sorted_top_line_data, chart_data_list

class RWWidgetDataService(WidgetDataService):
    '''
    Used for fetching key figures data from relief web
    '''

    def get_dataset_results(self):
        url = config.get('hdx.active_locations_toplines.url')
        top_line_data = []
        if url:
            rw = rw_access.RwAccess(url, self.country_name)
            top_line_data = rw.fetch_data()

            class RWGettersSetteres(formatters.FormatterGettersSetters):

                @staticmethod
                def top_line_date_set(r, value):
                    super(RWGettersSetteres, RWGettersSetteres).top_line_date_set(r, value)
                    r[u'datasetUpdateDate'] = value


                @staticmethod
                def spark_line_date_set(r, value):
                    r['formatted_date'] = value


            formatters.TopLineItemsWithDateFormatter(top_line_data, getter_setter_class=RWGettersSetteres,
                                                     src_date_format='%Y-%m-%dT%H:%M:%SZ').format_results()

        else:
            log.error('No value found for hdx.active_locations_toplines.url in ini file')

        return top_line_data, []


