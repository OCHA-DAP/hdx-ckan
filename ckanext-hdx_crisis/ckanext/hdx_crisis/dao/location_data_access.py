'''
Created on Dec 8, 2014

@author: alexandru-m-g
'''

import logging

import ckan.logic as logic
import ckan.model as model

import ckanext.hdx_crisis.dao.data_access as data_access
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters

from ckan.common import c

get_action = logic.get_action
DataAccess = data_access.DataAccess
log = logging.getLogger(__name__)


def get_formatted_topline_numbers(top_line_resource_id):
    '''
    Helper function that is actually a wrapper: it initializez a LocationDataAccess with the provided
    top_line_resource_id and then it applues the TopLineItemsWithDateFormatter over the results

    :param top_line_resource_id: the resource id which has a datastore with topline items
    :type top_line_resource_id: str
    :return: dictionary with formatted topline items
    :rtype: dict
    '''
    context = {'model': model, 'session': model.Session,
               'user': c.user or c.author, 'for_view': True,
               'auth_user_obj': c.userobj}

    loc_data_access = LocationDataAccess(top_line_resource_id)
    loc_data_access.fetch_data(context)
    top_line_items = loc_data_access.get_top_line_items()

    formatter = formatters.TopLineItemsWithDateFormatter(top_line_items)
    formatter.format_results()

    return top_line_items


class LocationDataAccess(DataAccess):

    def __init__(self, top_line_resource_id):
        self.resources_dict = {
            'top-line-numbers': {
                'resource_id': top_line_resource_id
            }
        }
