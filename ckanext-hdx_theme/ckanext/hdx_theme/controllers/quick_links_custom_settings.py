import json
import logging
import uuid

import ckan.lib.base as base
import ckan.lib.helpers as helpers
import ckan.logic as logic
import ckan.model as model
from ckan.common import _, request, response, g, c
from ckan.controllers.api import CONTENT_TYPES

log = logging.getLogger(__name__)
abort = base.abort


class QuickLinksCustomSettingsController(base.BaseController):
    def show(self):
        context = {u'user': g.user}
        logic.check_access('hdx_quick_links_update', context, {})

        setting_value = logic.get_action('hdx_quick_links_settings_show')({}, {})
        template_data = {
            'data': {
                'hdx.quick_links.config': json.dumps(setting_value)
            }
        }

        return base.render('admin/quick_links.html', extra_vars=template_data)

    def delete(self, id):
        context = {u'user': g.user}
        logic.check_access('hdx_quick_links_update', context, {})
        # delete_id = request.params.get('id')
        existing_setting_list = logic.get_action('hdx_quick_links_settings_show')({'not_initial': True}, {})
        remove_index, remove_element = self._find_quick_links_item_by_id(existing_setting_list, id)

        if remove_index >= 0:
            del existing_setting_list[remove_index]

        # if remove_element:
        #     self._remove_file_by_path(remove_element.get('graphic'))

        data_dict = {
            'hdx.quick_links.config': existing_setting_list
        }

        settings_json = logic.get_action('hdx_quick_links_settings_update')({}, data_dict)

        response.headers['Content-Type'] = CONTENT_TYPES['json']
        return settings_json

    def update(self):
        context = {u'user': g.user}
        logic.check_access('hdx_quick_links_update', context, {})

        item = self._process_request()

        if item:
            existing_setting_list = logic.get_action('hdx_quick_links_settings_show')({'not_initial': True}, {})
            # self._persist_file(item)

            if item.pop('new'):
                existing_setting_list.append(item)
            else:
                existing_index, existing_element = self._find_quick_links_item_by_id(existing_setting_list, item.get('id'))
                existing_setting_list[existing_index] = item

            data_dict = {
                'hdx.quick_links.config': self._sort_quick_links_items(existing_setting_list)
            }

            ret = logic.get_action('hdx_quick_links_settings_update')({}, data_dict)
        else:
            ret = json.dumps({
                'message': _('Badly formatted data')
            })

        response.headers['Content-Type'] = CONTENT_TYPES['json']
        return ret

    @staticmethod
    def _sort_quick_links_items(quick_links_items):
        return sorted(quick_links_items, key=lambda x: x.get('order'))

    @staticmethod
    def _find_quick_links_item_by_id(quick_links_items, id):
        index = -1
        element = None
        for i, item in enumerate(quick_links_items):
            if item.get('id') == id:
                index = i
                element = item
                break
        return index, element

    # def _delete_unneeded_files(self, settings_list):
    #     links_map = {item.get('graphic'): item for item in settings_list if item.get('graphic')}
    #     existing_setting_list = logic.get_action('hdx_quick_links_settings_show')({}, {})
    #     for item in existing_setting_list:
    #         if not links_map.get(item.get('graphic')):
    #             existing_upload = GlobalUpload({
    #                 'filename': item.get('graphic'),
    #                 'upload': None
    #             })
    #             existing_upload.delete()

    # def _remove_file_by_path(self, path):
    #     '''
    #     :param path: something like /global/[uuid].png
    #     '''
    #     if path:
    #         existing_upload = GlobalUpload({
    #             'filename': path,
    #             'upload': None
    #         })
    #         existing_upload.delete()

    # def _persist_file(self, item):
    #     # For some reason FieldStorage has the boolean value of false so we compare to None
    #     graphic_upload = item.get('graphic_upload')
    #     if graphic_upload is not None and graphic_upload != 'undefined':
    #
    #         # remove previous file if exists
    #         self._remove_file_by_path(item.get('graphic'))
    #
    #         upload = GlobalUpload({
    #             'filename': '{}_{}'.format(item.get('id')[0:4], unicode(uuid.uuid4())),
    #             'upload': graphic_upload
    #         })
    #         upload.upload()
    #         item['graphic'] = helpers.url_for('global_file_download', filename=upload.filename)
    #         del item['graphic_upload']

    @staticmethod
    def _process_request():
        '''
        :return: processes the request and returns a quick_links item
        :rtype: dict
        '''

        title = request.params.get('title')
        if not title:
            return None
        else:
            item = {
                'title': title,
                # 'description': request.params.get('description'),
                # 'graphic': request.params.get('graphic'),
                # 'graphic_upload': request.params.get('graphic_upload'),
                'url': request.params.get('url'),
                'order': int(request.params.get('order', -1)),
                'newTab': True if request.params.get('newTab') == 'true' else False,
                # 'embed': True if request.params.get('embed') == 'true' else False,
                'new': False if request.params.get('id') else True,
                'id': request.params.get('id') if request.params.get('id') else unicode(uuid.uuid4())
            }
            if request.params.get('buttonText'):
                item['buttonText'] = request.params.get('buttonText')

        return item
