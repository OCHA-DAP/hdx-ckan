import os

import pylons.config as config
from ckanext.hdx_theme.helpers.screenshot_creator import ScreenshotCreator

import ckan.lib.helpers as helpers
import ckan.lib.uploader as uploader
import ckan.logic as logic

get_action = logic.get_action
STORAGE_FOLDER = str(uploader.get_storage_path()) + '/storage/uploads/dataset/'

def __get_file_path(dataset_dict):
    return STORAGE_FOLDER + __get_file_name(dataset_dict)

def __get_file_name(dataset_dict):
    return '{}.jpg'.format(dataset_dict.get('id'))

def create_screenshot(dataset_dict):
    url = config.get('ckan.site_url') + \
          helpers.url_for('dataset_read', id=dataset_dict.get('name'))
    output_file = __get_file_path(dataset_dict)

    screenshot_creator = ScreenshotCreator(url, output_file, '"#map"', renderdelay=90000, waitcapturedelay=10000,
                                           mogrify=True, crop='548x400+311+0')
    screenshot_creator.execute()

def create_download_link(dataset_dict, default_value=None):
    if screenshot_exists(dataset_dict):
        url = helpers.url_for('dataset_image_serve', label=__get_file_name(dataset_dict))
        return url

    return default_value

def screenshot_exists(dataset_dict):
    output_file = __get_file_path(dataset_dict)
    exists = os.path.isfile(output_file)
    return exists
