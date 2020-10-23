'''
Created on Jul 07, 2015

@author: alexandru-m-g
'''
import logging
import requests
import datetime
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
from ckanext.hdx_package.helpers.resource_format import allowed_formats

from ckanext.hdx_theme.helpers.hash_generator import generate_hash_dict, HashCodeGenerator

log = logging.getLogger(__name__)

ZIPPED_SHAPEFILE_FORMAT = 'shp'
GEOJSON_FORMAT = 'geojson'
KML_FORMAT = 'kml'
KMZ_FORMAT = 'kmz'
GIS_FORMATS = [ZIPPED_SHAPEFILE_FORMAT, GEOJSON_FORMAT, KML_FORMAT, KMZ_FORMAT]

PROCESSING = 'processing'

_get_or_bust = logic.get_or_bust
get_action = logic.get_action


def detect_format_from_extension(url):
    available_formats = allowed_formats()
    if url:
        split_url = urlparse.urlsplit(url)
        if split_url.path:
            file_name = os.path.basename(split_url.path)
            possible_format = file_name.split(".")[-1].lower()
            if file_name.endswith('.shp.zip'):
                possible_format = 'zipped shapefile'

            # Needs to be an existing format
            if possible_format and possible_format in available_formats:
                return possible_format
    return None


def add_to_shape_info_list(shape_info_json, resource):
    if shape_info_json:
        try:
            existing_shape_info_json = resource.get('shape_info')
            if existing_shape_info_json:
                existing_shape_info = json.loads(existing_shape_info_json)
                if not isinstance(existing_shape_info, list):
                    existing_shape_info = [existing_shape_info]
            else:
                existing_shape_info = []
            shape_info_dict = json.loads(shape_info_json)
            shape_info_dict['timestamp'] = datetime.datetime.now().isoformat()
            existing_shape_info.append(shape_info_dict)

            #keep the list from growing indefinitely
            existing_shape_info = existing_shape_info[-10:]
            return json.dumps(existing_shape_info)

        except Exception, e:
            log.error('There was an error processing the shape info from geopreview: {}'.format(str(e)))

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
        log.error("Error in communication with geopreview stack")
        log.error(sys.exc_info()[0])
        shape_info = json.dumps({
            'state': 'failure',
            'message': 'Error in communication with geopreview stack',
            'layer_id': 'None',
            'error_type': 'ckan-generated-error',
            'error_class': 'None'
        })
    return shape_info


def add_init_shape_info_data_if_needed(resource_data):

    # all resources should have a name
    if 'name' not in resource_data:
        log.error('This resource does NOT have a name: {}'.format(str(resource_data)))

    # If this is the first time that a resource has been uploaded it might not have a format.
    # The format detection only happens during the actual 'create' action.
    # That's why we're applying the same format detection function to name and url in case there's no format provided.
    file_format = lower(resource_data.get('format', '')) or detect_format_from_extension(
        resource_data.get('name')) or detect_format_from_extension(resource_data.get('url'))

    if file_format in GIS_FORMATS:
        shape_info_json = json.dumps({
            'state': PROCESSING,
            'message': 'The processing of the geo-preview has started',
            'layer_id': 'None',
            'error_type': 'None',
            'error_class': 'None'
        })
        shape_info_list_json = add_to_shape_info_list(shape_info_json, resource_data)
        resource_data['shape_info'] = shape_info_list_json

def get_shape_info_state(resource_data):
    '''
    :param resource_data: a resource dict
    :type resource_data: dict
    :return: The current status of the transformation process. None if no "shape_info" property found
    :rtype: str
    '''

    shape_info_obj = get_latest_shape_info(resource_data)
    if shape_info_obj:
        return shape_info_obj.get('state')

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
        shape_info_list_json = add_to_shape_info_list(shape_info_json, result_dict)
        result_dict['shape_info'] = shape_info_list_json
        ctx['do_geo_preview'] = False
        get_action('resource_update')(ctx, result_dict)


def _before_ckan_action(context, resource_dict):
    '''
    :param context: context
    :type context: dict
    :param resource_dict:
    :type resource_dict dict
    '''

    do_geo_preview = context.get('do_geo_preview', True) and config.get('hdx.gis.layer_import_url') \
                     and not context.get('return_id_only')
    if do_geo_preview:
        # context['hdx_source_action'] = source_action
        add_init_shape_info_data_if_needed(resource_dict)


def _after_ckan_action(context, resource_dict):
    '''
    :param context: context
    :type context: dict
    :param resource_dict:
    :type resource_dict dict
    '''
    do_geo_preview = context.get('do_geo_preview', True) and config.get('hdx.gis.layer_import_url') \
                     and get_shape_info_state(resource_dict) == PROCESSING

    if do_geo_preview and lower(resource_dict.get('format', '')) in GIS_FORMATS:
        do_geo_transformation_process(context, resource_dict)


def get_latest_shape_info(resource_dict):
    if resource_dict:
        shape_info = resource_dict.get('shape_info')
        if shape_info:
            try:
                shape_info_obj = json.loads(shape_info)
                if isinstance(shape_info_obj, list):
                    return shape_info_obj[-1]
                else:
                    return shape_info_obj
            except ValueError, e:
                log.error("Couldn't load following string as json: {}".format(shape_info))
    return None


def geopreview_4_resources(original_resource_action):

    def resource_action(context, resource_dict):
        '''
        This runs the 'resource_create/resource_update' action from core ckan's create.py / update.py
        It triggers the geopreview creation process.
        '''

        # _before_ckan_action(context, resource_dict, 'resource_action')

        result_dict = original_resource_action(context, resource_dict)

        _after_ckan_action(context, result_dict)

        return result_dict

    return resource_action


def geopreview_4_packages(original_package_action):

    def package_action(context, package_dict):

        old_package_dict = get_action('package_show')(context, {'id': package_dict.get('id')}) \
            if 'id' in package_dict else {}

        old_resources_list = old_package_dict.get('resources')
        fields = ['name', 'description', 'url', 'format']
        resource_id_to_hash_dict = {}

        if old_resources_list:
            try:
                # We compute a hash code for "old" resource to see if they have changed
                resource_id_to_hash_dict = generate_hash_dict(old_resources_list, 'id', fields)
            except Exception, e:
                log.error(str(e))

        for resource_dict in package_dict.get('resources', []):
            modified_or_new = True
            try:
                if 'id' in resource_dict:
                    rid = resource_dict['id']
                    hash_code = HashCodeGenerator(resource_dict, fields).compute_hash()
                    modified_or_new = False if resource_id_to_hash_dict.get(rid) == hash_code else True
            except Exception, e:
                log.error(str(e))

            if modified_or_new:
                _before_ckan_action(context, resource_dict)

        result_dict = original_package_action(context, package_dict)

        # If it comes from resource_create / resource_update the transaction is not yet committed
        # (resource is not yet saved )
        if isinstance(result_dict, dict):
            if not context.get('defer_commit', False):
                for resource_dict in result_dict.get('resources', []):
                    _after_ckan_action(context, resource_dict)
        else:
            log.info("result_dict variable is not a dict but: {}".format(str(result_dict)))

        return result_dict

    return package_action
