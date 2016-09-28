'''
Created on Jul 07, 2015

@author: alexandru-m-g
'''
import logging
import requests
import sys
import json
import urllib
import urlparse
import os
from string import lower
from pylons import config

import ckan.logic as logic
import ckan.model as model
import ckan.lib.helpers as h

from ckan.common import c

log = logging.getLogger(__name__)

ZIPPED_SHAPEFILE_FORMAT = 'zipped shapefile'
GEOJSON_FORMAT = 'geojson'
KML_FORMAT = 'kml'
KMZ_FORMAT = 'kmz'
GIS_FORMATS = [ZIPPED_SHAPEFILE_FORMAT, GEOJSON_FORMAT, KML_FORMAT, KMZ_FORMAT]

PROCESSING = 'processing'

_get_or_bust = logic.get_or_bust
get_action = logic.get_action

def detect_format_from_extension(url):
    if url:
        split_url = urlparse.urlsplit(url)
        if split_url.path:
            file_name = os.path.basename(split_url.path)
            possible_extension = file_name.split(".")[-1].lower()
            if file_name.endswith('.shp.zip'):
                return 'zipped shapefile'
            elif '.' in file_name and possible_extension:
                return possible_extension
    return None


def _get_shape_info_as_json(gis_data):
    resource_id = gis_data['resource_id']

    layer_import_url = config.get('hdx.gis.layer_import_url')
    encoded_download_url = urllib.quote_plus(gis_data['url'])
    gis_url = layer_import_url.format(dataset_id=gis_data['dataset_id'], resource_id=resource_id,
                                      resource_download_url=encoded_download_url, url_type=gis_data['url_type'])
    # gis_url = layer_import_url.replace("{dataset_id}", gis_data['dataset_id']).replace("{resource_id}",
    #                                                                                    resource_id).replace(
    #     "{resource_download_url}", gis_data['url'])
    result = _make_geopreview_request(gis_url)
    return result


def _make_geopreview_request(gis_url):
    try:
        response = requests.get(gis_url, allow_redirects=True)
        shape_info = response.text if hasattr(response, 'text') else ''
    except:
        log.error("Error retrieving the shape info content")
        log.error(sys.exc_info()[0])
        shape_info = json.dumps({
            'state': 'failure',
            'message': 'Error retrieving the shape info content',
            'layer_id': 'None',
            'error_type': 'ckan-generated-error',
            'error_class': 'None'
        })
    return shape_info


def add_init_shape_info_data_if_needed(resource_data):

    # If this is the first time that a resource has been uploaded it might not have a format.
    # The format detection only happens during the actual 'create' action.
    # That's why we're applying the same format detection function to name and url in case there's no format provided.
    file_format = lower(resource_data.get('format', '')) or detect_format_from_extension(
        resource_data['name']) or detect_format_from_extension(resource_data['url'])

    if file_format in GIS_FORMATS:
        shape_info = json.dumps({
            'state': PROCESSING,
            'message': 'The processing of the geo-preview has started',
            'layer_id': 'None',
            'error_type': 'None',
            'error_class': 'None'
        })

        resource_data['shape_info'] = shape_info

def get_shape_info_state(resource_data):
    '''
    :param resource_data: a resource dict
    :type resource_data: dict
    :return: The current status of the transformation process. None if no "shape_info" property found
    :rtype: str
    '''

    shape_info_str = resource_data.get('shape_info')
    if shape_info_str:
        try:
            shape_info = json.loads(shape_info_str)
            return shape_info.get('state')
        except ValueError, e:
            log.error("Couldn't load following string as json: {}".format(shape_info_str))
    return None

def do_geo_transformation_process(context, result_dict):
    '''
    :param context:
    :type context:
    :param result_dict:
    :type result_dict:
    :return: False if some problem appeared, True otherwise
    :rtype: bool
    '''

    user = context.get('user') or c.user or c.author

    ctx = {'model': model, 'session': model.Session,
               'api_version': 3, 'for_edit': True,
               'user': user}

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
        ctx['do_geo_preview'] = False
        get_action('resource_update')(ctx, result_dict)


def _before_ckan_action(context, resource_dict, source_action):
    '''
    'source_action' helps to only trigger geopreview process for the resource(s) that are updated.
    resource_create() calls package_update() and the package could have several resources.

    :param context: context
    :type context: dict
    :param resource_dict:
    :type resource_dict dict
    :param source_action: either 'resource_action' or 'package_action' - the initial trigger of the create/update
    :type source_action: str
    '''
    context['hdx_source_action'] = source_action
    do_geo_preview = context.get('do_geo_preview', True) and config.get('hdx.gis.layer_import_url') \
                     and get_shape_info_state(resource_dict) != PROCESSING and not context.get('return_id_only')
    if do_geo_preview:
        add_init_shape_info_data_if_needed(resource_dict)


def _after_ckan_action(context, resource_dict, source_action):
    do_geo_preview = context.get('do_geo_preview', True) and config.get('hdx.gis.layer_import_url') \
                     and get_shape_info_state(resource_dict) == PROCESSING \
                     and context.get('source_action') == source_action

    if do_geo_preview and lower(resource_dict.get('format', '')) in GIS_FORMATS:
        do_geo_transformation_process(context, resource_dict)


def geopreview_4_resources(original_resource_action):

    def resource_action(context, resource_dict):
        '''
        This runs the 'resource_create/resource_update' action from core ckan's create.py / update.py
        It triggers the geopreview creation process.
        '''

        _before_ckan_action(context, resource_dict, 'resource_action')

        result_dict = original_resource_action(context, resource_dict)

        _after_ckan_action(context, result_dict, 'resource_action')

        return result_dict

    return resource_action


def geopreview_4_packages(original_package_action):

    def package_action(context, package_dict):

        for resource_dict in package_dict.get('resources', []):
            _before_ckan_action(context, resource_dict, 'package_action')

        result_dict = original_package_action(context, package_dict)

        if isinstance(result_dict, dict):
            for resource_dict in result_dict.get('resources', []):
                _after_ckan_action(context, resource_dict, 'package_action')
        else:
            log.info("result_dict variable is not a dict but: {}".format(str(result_dict)))

        return result_dict

    return package_action