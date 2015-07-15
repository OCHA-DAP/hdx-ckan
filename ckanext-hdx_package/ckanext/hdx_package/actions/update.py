'''
Created on Jul 07, 2015

@author: alexandru-m-g
'''

import ckan.logic as logic
import ckan.logic.action.update as core_update

import ckanext.hdx_package.helpers.geopreview as geopreview

from string import lower
from pylons import config

_get_or_bust = logic.get_or_bust
get_action = logic.get_action


def resource_update(context, data_dict):
    '''
    This runs the 'resource_update' action from core ckan's update.py
    It was modified to trigger the geopreview creation process.
    '''
    do_geo_preview = context.get('do_geo_preview', True) and config.get('hdx.gis.layer_import_url')
    if do_geo_preview:
        geopreview.add_init_shape_info_data_if_needed(data_dict)

    result_dict = core_update.resource_update(context, data_dict)

    if do_geo_preview and lower(data_dict.get('format', '')) in geopreview.GIS_FORMATS:
        geopreview.do_geo_transformation_process(result_dict)
