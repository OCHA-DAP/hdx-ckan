'''
Created on Jul 07, 2015

@author: alexandru-m-g
'''
import json
from string import lower
from pylons import config
from ckanext.hdx_package.actions.create import get_action, _get_or_bust

ZIPPED_SHAPEFILE_FORMAT = 'zipped shapefile'
GEOJSON_FORMAT = 'geojson'
GIS_FORMATS = [ZIPPED_SHAPEFILE_FORMAT, GEOJSON_FORMAT]


def _get_shape_info_as_json(gis_data):
    resource_id = gis_data['resource_id']
    resource_id = resource_id if resource_id and resource_id.strip() else 'new'

    layer_import_url = config.get('hdx.gis.layer_import_url')
    gis_url = layer_import_url.replace("{dataset_id}", gis_data['dataset_id']).replace("{resource_id}",
                                                                                       resource_id).replace(
        "{resource_download_url}", gis_data['url'])
    result = get_action('hdx_get_shape_info')({}, {"gis_url": gis_url})
    return result


def add_init_shape_info_data_if_needed(resource_data):
    if 'format' in resource_data and lower(resource_data['format']) in GIS_FORMATS:
        shape_info = json.dumps({
            'state': 'processing',
            'message': 'The processing of the geo-preview has started',
            'layer_id': 'None',
            'error_type': 'None',
            'error_class': 'None'
        })

        resource_data['shape_info'] = shape_info


def start_geo_transformation_process(context, result_dict):
    '''
    :param context:
    :type context:
    :param result_dict:
    :type result_dict:
    :return: False if some problem appeared, True otherwise
    :rtype: bool
    '''
    dataset_id = _get_or_bust(result_dict, 'package_id')
    resource_id = result_dict['id']
    gis_data = {
        'dataset_id': dataset_id,
        'resource_id': resource_id,
        'url': result_dict['url']
    }
    shape_info_json = _get_shape_info_as_json(gis_data)
    shape_info = json.loads(shape_info_json)
    if shape_info.get('error_type') in ['transformation-init-problem', 'ckan-generated-error']:
        result_dict['shape_info'] = shape_info_json
        context['do_geo_preview'] = False
        return False
    return True