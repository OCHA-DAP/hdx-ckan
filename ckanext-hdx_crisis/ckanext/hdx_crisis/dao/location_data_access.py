'''
Created on Dec 8, 2014

@author: alexandru-m-g
'''

import logging

import ckan.logic as logic

import ckanext.hdx_crisis.dao.data_access as data_access

get_action = logic.get_action
DataAccess = data_access.DataAccess
log = logging.getLogger(__name__)


class LocationDataAccess(DataAccess):

    def __init__(self, top_line_resource_id):
        self.resources_dict = {
            'top-line-numbers': {
                'resource_id': top_line_resource_id
            }
        }
