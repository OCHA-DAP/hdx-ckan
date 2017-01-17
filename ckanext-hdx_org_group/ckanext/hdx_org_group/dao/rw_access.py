
import ckan.logic as logic
import ckan.lib.helpers as h
import ckanext.hdx_org_group.dao.common_functions as common_functions

from ckanext.hdx_theme.helpers.top_line_items_formatter import TopLineItemsWithDateFormatter

_get_action = logic.get_action

class RwAccess(object):
    def __init__(self, resource_dict, location_iso):
        self.resource_dict = resource_dict
        self.dataset_link = h.url_for('dataset_read', id=resource_dict['package_id'])
        self.location_iso = location_iso

    def fetch_data(self):
        location_list = _get_action('hdx_get_locations_info_from_rw')({}, {'rw_url': self.resource_dict['url']})

        location = self.__find_current_location(location_list)

        toplines = []
        if location:
            toplines = self.__transform_to_toplines(location)
        return toplines

    def __find_current_location(self, location_list):
        '''
        :param location_list:
        :type location_list: list
        :return: current location if found othewise None
        :rtype: dict
        '''
        if location_list:
            for location in location_list:
                if location.get('iso3', '').lower() == self.location_iso:
                    return location

        return None

    def __transform_to_toplines(self, location):
        toplines = []
        for figure in location.get('figures', []):
            topline = self.__transform_to_topline(location, figure)
            toplines.append(topline)

        return toplines

    def __transform_to_topline(self, location, figure):

        ret_dict = {
            # 'datasetUpdateDate': '',
            # 'unitName': '',
            # 'unitCode': u'people',
            'sourceName': figure.get('source'),
            'sourceCode': figure.get('source'),
            'indicatorTypeName': figure.get('name'),
            'indicatorTypeCode': figure.get('name'),
            # 'formatted_value': '6,201,521',
            'value': float(figure.get('value')),
            'datasetLink': self.dataset_link,
            'reliefWebLink': figure.get('url'),
            'time': figure.get('date'),
            'latest_date': figure.get('date'),
            'locationName': location.get('name'),
            'locationCode': self.location_iso,
            'sparklines': figure.get('values'),
            'units': 'count'
        }
        value = ret_dict.get('value')
        ret_dict['units'] = ret_dict['unitName'] = common_functions.compute_simplifying_units(value)

        return ret_dict

    @staticmethod
    def __get_sparklines_from_figure(figure):
        pass