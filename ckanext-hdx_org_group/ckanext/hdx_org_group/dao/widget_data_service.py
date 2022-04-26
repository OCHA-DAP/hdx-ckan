import logging


import ckan.plugins.toolkit as tk
import ckan.model as model
import ckan.logic as logic

import ckanext.hdx_org_group.dao.indicator_access as indicator_access
import ckanext.hdx_org_group.dao.rw_access as rw_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters

log = logging.getLogger(__name__)

_get_action = tk.get_action
config = tk.config


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
            country_id, None, recompute_units=True)

        top_line_data = top_line_dao.fetch_indicator_data_for_country()

        if not top_line_data:
            log.warn(
                'No top line numbers found for country: {}'.format(country_id))
            top_line_data = []

        class CustomFormatters(formatters.FormatterGettersSetters):
            @staticmethod
            def top_line_date_set(r, value):
                r['datasetUpdateDate'] = value

            @staticmethod
            def top_line_date_get(r):
                return r['date']

        formatters.TopLineItemsWithDateFormatter(top_line_data, getter_setter_class=CustomFormatters,
                                                 src_date_format='%Y-%m-%d').format_results()

        return top_line_data


class RWWidgetDataService(WidgetDataService):
    '''
    Used for fetching key figures data from relief web
    '''

    def get_dataset_results(self):
        context = {'model': model, 'session': model.Session}
        resource_id = config.get('hdx.active_locations_reliefweb.resource_id')
        try:
            resource_dict = _get_action('resource_show')(context, {'id': resource_id})
        except logic.NotFound as e:
            resource_dict = None
            log.error(
                'No resource was found for "hdx.active_locations_reliefweb.resource_id" = {}. Exception: NotFound'.format(
                    resource_id))
        top_line_data = []
        if resource_dict:
            rw = rw_access.RwAccess(resource_dict, self.country_name)
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

        return top_line_data
