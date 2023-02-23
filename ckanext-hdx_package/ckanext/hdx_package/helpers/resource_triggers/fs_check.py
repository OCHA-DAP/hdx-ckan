'''
Created on August 24, 2022

@author: dan
'''
import datetime
import json
import logging
import sys

import requests
import six.moves.urllib.parse as urlparse
from werkzeug.datastructures import FileStorage as FlaskFileStorage

import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

PROCESSING = 'processing'

_get_or_bust = tk.get_or_bust
get_action = tk.get_action

config = tk.config


def _is_upload_xls(resource_dict):
    if resource_dict and 'upload' in resource_dict:
        return isinstance(resource_dict.get('upload'), FlaskFileStorage) and 'xls' in resource_dict.get('format',
                                                                                                        '').lower()


def _before_ckan_action(context, resource_dict):
    '''
    :param context: context
    :type context: dict
    :param resource_dict:
    :type resource_dict dict
    '''
    is_upload_xls = _is_upload_xls(resource_dict)
    if is_upload_xls:
        context['allow_fs_check_field'] = True
        resource_dict['fs_check_info'] = {
            'state': PROCESSING,
            'message': 'The processing of the file structure check has started',
            # 'error_type': 'None',
            # 'error_class': 'None',
            'timestamp': datetime.datetime.now().isoformat()
        }
    else:
        context['allow_fs_check_field'] = False
    # log.info("in before fs_check")
    context['fs_check_is_upload_xls'] = is_upload_xls


def _after_ckan_action(context, resource_dict):
    '''
    :param context: context
    :type context: dict
    :param resource_dict:
    :type resource_dict dict
    '''
    if context.get('fs_check_is_upload_xls'):
        _file_structure_check(resource_dict)
    context.pop('fs_check_is_upload_xls', None)
    log.info("in after ckan action in fs_check")


def fs_check_4_resources(original_resource_action):
    def resource_action(context, resource_dict):
        '''
        This runs the 'resource_create/resource_update' action from core ckan's create.py / update.py
        It triggers the file structure check creation process.
        '''

        is_upload_xls = _before_ckan_action(context, resource_dict)

        result_dict = original_resource_action(context, resource_dict)

        _after_ckan_action(context, result_dict, is_upload_xls)

        return result_dict

    return resource_action


def _file_structure_check(data_dict):
    file_structure_check_url = config.get('hdx.file_structure.check_url')
    encoded_download_url = urlparse.quote_plus(data_dict['url'])
    hxl_proxy_source_info_url = config.get('hdx.hxlproxy.source_info_url').format(url=data_dict['url'])
    fs_check_url = file_structure_check_url.format(dataset_id=data_dict.get('package_id'),
                                                   resource_id=data_dict.get('id'),
                                                   url_type=data_dict.get('url_type'),
                                                   url=encoded_download_url,
                                                   hxl_proxy_source_info_url=hxl_proxy_source_info_url)
    return _make_file_structure_check_request(fs_check_url)


def _make_file_structure_check_request(fs_check_url):
    try:
        log.info(fs_check_url)
        response = requests.get(fs_check_url, allow_redirects=True)
        fs_check_info = response.text if hasattr(response, 'text') else ''
    except Exception as ex:
        log.error("Error in communication with fs_check stack")
        log.error(ex)
        log.error(sys.exc_info()[0])
        fs_check_info = json.dumps({
            'state': 'failure',
            'message': 'Error in communication with fs_check stack',
            'error_type': 'ckan-generated-error',
            'error_class': 'None'
        })
    return fs_check_info
