'''
Created on Jul 07, 2015

@author: alexandru-m-g
'''

from pylons import config
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

    do_geo_preview = config.get('hdx.gis.layer_import_url')
    if do_geo_preview:
        geopreview.add_init_shape_info_data_if_needed(data_dict)

    result_dict = core_create.resource_create(context, data_dict)

    if do_geo_preview and lower(result_dict.get('format', '')) in geopreview.GIS_FORMATS:
        started_successfully = geopreview.start_geo_transformation_process(context, result_dict)
        if not started_successfully:
            get_action('resource_update')(context, result_dict)
