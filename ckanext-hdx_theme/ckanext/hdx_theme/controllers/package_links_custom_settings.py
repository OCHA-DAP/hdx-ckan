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


class PackageLinksCustomSettingsController(base.BaseController):
    def show(self):
        context = {u'user': g.user}
        logic.check_access('hdx_quick_links_update', context, {})

        setting_value = logic.get_action('hdx_package_links_settings_show')({}, {})
        template_data = {
            'data': {
                'hdx.package_links.config': json.dumps(setting_value)
            }
        }

        return base.render('admin/package_links.html', extra_vars=template_data)

    def delete(self, id):
        context = {u'user': g.user}
        logic.check_access('hdx_quick_links_update', context, {})
        # delete_id = request.params.get('id')
        existing_setting_list = logic.get_action('hdx_package_links_settings_show')({'not_initial': True}, {})
        remove_index, remove_element = self._find_package_links_item_by_id(existing_setting_list, id)

        if remove_index >= 0:
            del existing_setting_list[remove_index]

        # if remove_element:
        #     self._remove_file_by_path(remove_element.get('graphic'))

        data_dict = {
            'hdx.package_links.config': existing_setting_list
        }

        settings_json = logic.get_action('hdx_package_links_settings_update')({}, data_dict)

        response.headers['Content-Type'] = CONTENT_TYPES['json']
        return settings_json

    def update(self):
        context = {u'user': g.user}
        logic.check_access('hdx_quick_links_update', context, {})

        item = self._process_request()

        if item:
            existing_setting_list = logic.get_action('hdx_package_links_settings_show')({'not_initial': True}, {})
            # self._persist_file(item)

            if item.pop('new'):
                existing_setting_list.append(item)
            else:
                existing_index, existing_element = self._find_package_links_item_by_id(existing_setting_list, item.get('id'))
                existing_setting_list[existing_index] = item

            data_dict = {
                'hdx.package_links.config': self._sort_package_links_items(existing_setting_list)
            }

            ret = logic.get_action('hdx_package_links_settings_update')({}, data_dict)
        else:
            ret = json.dumps({
                'message': _('Badly formatted data')
            })

        response.headers['Content-Type'] = CONTENT_TYPES['json']
        return ret

    @staticmethod
    def _sort_package_links_items(package_links_items):
        return sorted(package_links_items, key=lambda x: x.get('order'))

    @staticmethod
    def _find_package_links_item_by_id(package_links_items, id):
        index = -1
        element = None
        for i, item in enumerate(package_links_items):
            if item.get('id') == id:
                index = i
                element = item
                break
        return index, element

    @staticmethod
    def _process_request():
        '''
        :return: processes the request and returns a package_links item
        :rtype: dict
        '''

        title = request.params.get('title')
        if not title:
            return None
        else:
            item = {
                'title': title,
                'url': request.params.get('url'),
                'order': int(request.params.get('order', -1)),
                'newTab': True if request.params.get('newTab') == 'true' else False,
                'package_list': request.params.get('package_list').replace(' ', ''),
                # 'embed': True if request.params.get('embed') == 'true' else False,
                'new': False if request.params.get('id') else True,
                'id': request.params.get('id') if request.params.get('id') else unicode(uuid.uuid4())
            }
            if request.params.get('buttonText'):
                item['buttonText'] = request.params.get('buttonText')

        return item
