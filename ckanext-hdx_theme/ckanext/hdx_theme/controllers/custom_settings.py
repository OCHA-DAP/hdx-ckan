import json
import logging
import uuid

from ckanext.hdx_theme.helpers.uploader import GlobalUpload

import ckan.lib.base as base
import ckan.lib.helpers as helpers
import ckan.logic as logic
from ckan.common import _, request, response
from ckan.controllers.api import CONTENT_TYPES

log = logging.getLogger(__name__)


class CustomSettingsController(base.BaseController):
    def show(self):

        logic.check_access('config_option_show', {}, {})

        setting_value = logic.get_action('hdx_carousel_settings_show')({}, {})
        template_data = {
            'data': {
                'hdx.carousel.config': json.dumps(setting_value)
            }
        }

        return base.render('admin/carousel.html', extra_vars=template_data)

    def delete(self):
        logic.check_access('config_option_update', {}, {})
        delete_id = request.params.get('id')
        existing_setting_list = logic.get_action('hdx_carousel_settings_show')({'not_initial': True}, {})
        remove_index, remove_element = self._find_carousel_item_by_id(existing_setting_list, delete_id)

        if remove_index >= 0:
            del existing_setting_list[remove_index]

        if remove_element and remove_element.get('graphic'):
            existing_upload = GlobalUpload({
                'filename': remove_element.get('graphic'),
                'upload': None
            })
            existing_upload.delete()

        data_dict = {
            'hdx.carousel.config': existing_setting_list
        }

        settings_json = logic.get_action('hdx_carousel_settings_update')({}, data_dict)

        response.headers['Content-Type'] = CONTENT_TYPES['json']
        return settings_json

    def update(self):
        logic.check_access('config_option_update', {}, {})

        item = self._process_request()

        if item:
            existing_setting_list = logic.get_action('hdx_carousel_settings_show')({'not_initial': True}, {})
            self._persist_file(item)

            if item.pop('new'):
                existing_setting_list.append(item)
            else:
                existing_index, existing_element = self._find_carousel_item_by_id(existing_setting_list, item.get('id'))
                existing_setting_list[existing_index] = item

            data_dict = {
                'hdx.carousel.config': self._sort_carousel_items(existing_setting_list)
            }

            ret = logic.get_action('hdx_carousel_settings_update')({}, data_dict)
        else:
            ret = json.dumps({
                'message': _('Badly formatted data')
            })

        response.headers['Content-Type'] = CONTENT_TYPES['json']
        return ret

    @staticmethod
    def _sort_carousel_items(carousel_items):
        return sorted(carousel_items, key=lambda x: x.get('order'))

    @staticmethod
    def _find_carousel_item_by_id(carousel_items, id):
        index = -1
        element = None
        for i, item in enumerate(carousel_items):
            if item.get('id') == id:
                index = i
                element = item
                break
        return index, element

    # def _delete_unneeded_files(self, settings_list):
    #     links_map = {item.get('graphic'): item for item in settings_list if item.get('graphic')}
    #     existing_setting_list = logic.get_action('hdx_carousel_settings_show')({}, {})
    #     for item in existing_setting_list:
    #         if not links_map.get(item.get('graphic')):
    #             existing_upload = GlobalUpload({
    #                 'filename': item.get('graphic'),
    #                 'upload': None
    #             })
    #             existing_upload.delete()

    def _persist_file(self, item):
        # For some reason FieldStorage has the boolean value of false so we compare to None
        graphic_upload = item.get('graphic_upload')
        if graphic_upload is not None and graphic_upload != 'undefined':
            upload = GlobalUpload({
                'filename': None,
                'upload': graphic_upload
            })
            upload.upload()
            item['graphic'] = helpers.url_for('global_file_download', filename=upload.filename)
            del item['graphic_upload']

    @staticmethod
    def _process_request():
        '''
        :return: processes the request and returns a carousel item
        :rtype: dict
        '''

        title = request.params.get('title')
        if not title:
            return None
        else:
            item = {
                'title': title,
                'description': request.params.get('description'),
                'graphic': request.params.get('graphic'),
                'graphic_upload': request.params.get('graphic_upload'),
                'url': request.params.get('url'),
                'order': int(request.params.get('order', -1)),
                'newTab': True if request.params.get('newTab') else False,
                'embed': True if request.params.get('embed') else False,
                'new': False if request.params.get('id') else True,
                'id': request.params.get('id') if request.params.get('id') else unicode(uuid.uuid4())
            }
            if request.params.get('buttonText'):
                item['buttonText'] = request.params.get('buttonText')

        return item
