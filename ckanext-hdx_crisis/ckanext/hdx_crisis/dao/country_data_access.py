'''
Created on Dec 8, 2014

@author: alexandru-m-g
'''

import logging

import ckan.logic as logic

import ckanext.hdx_crisis.dao.data_access as data_access

get_action = logic.get_action

log = logging.getLogger(__name__)


class ColombiaCrisisDataAccess(data_access.CrisisDataAccess):

    def __init__(self):
        self.resources_dict = {
            'top-line-numbers': {
                'dataset': 'topline-colombia-figures',
                'resource': 'topline-colombia-figures.csv'
            }
        }
