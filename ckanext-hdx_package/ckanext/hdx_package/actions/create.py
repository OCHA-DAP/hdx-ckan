'''
Created on Jul 07, 2015

@author: alexandru-m-g
'''

from string import lower

import ckan.logic.action.create as core_create
import ckan.logic as logic
import ckanext.hdx_package.helpers.geopreview as geopreview

_get_or_bust = logic.get_or_bust
get_action = logic.get_action


def resource_create(context, data_dict):
    '''
    This runs the 'resource_create' action from core ckan's create.py
    It was modified to trigger the geopreview creation process.
    '''

    geopreview.add_init_shape_info_data_if_needed(data_dict)

    result_dict = core_create.resource_create(context, data_dict)

    if lower(result_dict.get('format', '')) in geopreview.GIS_FORMATS:
        problem_appeared = geopreview.start_geo_transformation_process(context, result_dict)
        if problem_appeared:
            get_action('resource_update')(context, result_dict)
