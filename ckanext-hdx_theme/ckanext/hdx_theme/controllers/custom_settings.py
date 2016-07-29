import logging

import ckan.lib.base as base
import ckan.logic as logic
import ckan.lib.helpers as helpers

from ckan.common import _, c, g, request, response
from ckan.controllers.api import CONTENT_TYPES

from ckanext.hdx_theme.helpers.uploader import GlobalUpload

log = logging.getLogger(__name__)


class CustomSettingsController(base.BaseController):
    def show(self):

        logic.check_access('config_option_show', {}, {})

        setting_value = logic.get_action('hdx_carousel_settings_show')({}, {})
        template_data = {
            'data': {
                'hdx.carousel.config': setting_value
            }
        }

        return base.render('settings/carousel_settings.html', extra_vars=template_data)

    def update(self):
        logic.check_access('config_option_update', {}, {})

        settings_list = self._process_request()

        self._delete_unneeded_files(settings_list)
        self._persist_files(settings_list)

        data_dict = {
            'hdx.carousel.config': settings_list
        }

        settings_json = logic.get_action('hdx_carousel_settings_show')({}, data_dict)

        response.headers['Content-Type'] = CONTENT_TYPES['json']
        return settings_json

    def _delete_unneeded_files(self, settings_list):
        links_map = {item.get('graphic_url'): item for item in settings_list if item.get('graphic_url')}
        existing_setting_list = logic.get_action('hdx_carousel_settings_show')({}, {})
        for item in existing_setting_list:
            if not links_map.get(item.get('graphics_url')):
                existing_upload = GlobalUpload({
                    'filename': item.get('graphics_url'),
                    'upload': None
                })
                existing_upload.delete()

    def _persist_files(self, settings_list):
        for item in settings_list:
            if item.get('graphic_upload'):
                upload = GlobalUpload({
                    'filename': None,
                    'upload': item.get('graphic_upload')
                })
                upload.upload()
                item['graphics_url'] = helpers.url_for('global_file_download', filename=upload.filename)
                del item['graphic_upload']

    @staticmethod
    def _process_request():
        '''
        :return: processes the request and returns a list of settings of each carousel item
        :rtype: list of dict
        '''

        result = []

        for i in range(1, 21):
            title = request.params.get('title_{}', format(i))
            if not title:
                break
            else:
                item = {
                    'title': title,
                    'description': request.params.get('descritpion_{}', format(i)),
                    'graphic_url': request.params.get('graphic_url_{}', format(i)),
                    'graphic_upload': request.params.get('graphic_upload_{}', format(i)),
                    'url': request.params.get('url_{}', format(i))
                }
                result.append(item)

        return result

