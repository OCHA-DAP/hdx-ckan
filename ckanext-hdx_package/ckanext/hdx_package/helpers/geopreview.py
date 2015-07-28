'''
Created on Jul 07, 2015

@author: alexandru-m-g
'''
import json
import urllib
from string import lower
from pylons import config

import ckan.logic as logic
import ckan.model as model
import ckan.lib.helpers as h

from ckan.common import c

ZIPPED_SHAPEFILE_FORMAT = 'zipped shapefile'
GEOJSON_FORMAT = 'geojson'
KML_FORMAT = 'kml'
GIS_FORMATS = [ZIPPED_SHAPEFILE_FORMAT, GEOJSON_FORMAT, KML_FORMAT]

_get_or_bust = logic.get_or_bust
get_action = logic.get_action


def _get_shape_info_as_json(gis_data):
    resource_id = gis_data['resource_id']
    resource_id = resource_id if resource_id and resource_id.strip() else 'new'

    layer_import_url = config.get('hdx.gis.layer_import_url')
    encoded_download_url = urllib.quote_plus(gis_data['url'])
    gis_url = layer_import_url.format(dataset_id=gis_data['dataset_id'], resource_id=resource_id,
                                      resource_download_url=encoded_download_url, url_type=gis_data['url_type'])
    # gis_url = layer_import_url.replace("{dataset_id}", gis_data['dataset_id']).replace("{resource_id}",
    #                                                                                    resource_id).replace(
    #     "{resource_download_url}", gis_data['url'])
    result = get_action('hdx_get_shape_info')({}, {"gis_url": gis_url})
    return result


def add_init_shape_info_data_if_needed(resource_data):
    if lower(resource_data.get('format', '')) in GIS_FORMATS:
        shape_info = json.dumps({
            'state': 'processing',
            'message': 'The processing of the geo-preview has started',
            'layer_id': 'None',
            'error_type': 'None',
            'error_class': 'None'
        })

        resource_data['shape_info'] = shape_info


def do_geo_transformation_process(result_dict):
    '''
    :param context:
    :type context:
    :param result_dict:
    :type result_dict:
    :return: False if some problem appeared, True otherwise
    :rtype: bool
    '''

    context = {'model': model, 'session': model.Session,
               'api_version': 3, 'for_edit': True,
               'user': c.user or c.author, 'auth_user_obj': c.userobj}

    url = result_dict['url']

    # This is needed because the URL is not always correctly set in the received dictionary
    if result_dict.get('url_type', '') == 'upload' and 'http' not in url:
        url = h.url_for(controller='package',
                  action='resource_download',
                  id=result_dict['package_id'],
                  resource_id=result_dict['id'],
                  filename=url,
                  qualified=True)
    # result_dict = get_action('resource_show')(context, {'id': resource_dict['id']})

    dataset_id = _get_or_bust(result_dict, 'package_id')
    resource_id = result_dict['id']
    gis_data = {
        'dataset_id': dataset_id,
        'resource_id': resource_id,
        'url': url,
        'url_type': result_dict.get('url_type', 'api')
    }
    shape_info_json = _get_shape_info_as_json(gis_data)
    shape_info = json.loads(shape_info_json)
    if shape_info.get('error_type') in ['transformation-init-problem', 'ckan-generated-error']:
        result_dict['shape_info'] = shape_info_json
        context['do_geo_preview'] = False
        get_action('resource_update')(context, result_dict)