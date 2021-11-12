import flask
import json
import logging
import uuid

from six import text_type

import ckan.plugins.toolkit as tk

from ckanext.hdx_theme.helpers.uploader import GlobalUpload

abort = tk.abort
_ = tk._
g = tk.g
h = tk.h
request = tk.request
check_access = tk.check_access
get_action = tk.get_action
render = tk.render

log = logging.getLogger(__name__)

hdx_quick_links = flask.Blueprint(u'hdx_quick_links', __name__, url_prefix=u'/ckan-admin/dataviz')


def show():
    context = {u'user': g.user}
    check_access('hdx_quick_links_update', context, {})

    setting_value = get_action('hdx_quick_links_settings_show')({}, {})
    template_data = {
        'data': {
            'hdx.quick_links.config': json.dumps(setting_value)
        }
    }

    return render('admin/quick_links.html', extra_vars=template_data)


def delete(id):
    context = {u'user': g.user}
    check_access('hdx_quick_links_update', context, {})
    # delete_id = request.params.get('id')
    existing_setting_list = get_action('hdx_quick_links_settings_show')({'not_initial': True}, {})
    remove_index, remove_element = _find_quick_links_item_by_id(existing_setting_list, id)

    if remove_index >= 0:
        del existing_setting_list[remove_index]

    # if remove_element:
    #     self._remove_file_by_path(remove_element.get('graphic'))

    data_dict = {
        'hdx.quick_links.config': existing_setting_list
    }

    settings_json = get_action('hdx_quick_links_settings_update')({}, data_dict)

    # response.headers['Content-Type'] = CONTENT_TYPES['json']
    return settings_json


def update():
    context = {u'user': g.user}
    check_access('hdx_quick_links_update', context, {})

    item = _process_request()

    if item:
        existing_setting_list = get_action('hdx_quick_links_settings_show')({'not_initial': True}, {})
        # self._persist_file(item)

        if item.pop('new'):
            existing_setting_list.append(item)
        else:
            existing_index, existing_element = _find_quick_links_item_by_id(existing_setting_list, item.get('id'))
            existing_setting_list[existing_index] = item

        data_dict = {
            'hdx.quick_links.config': _sort_quick_links_items(existing_setting_list)
        }

        ret = get_action('hdx_quick_links_settings_update')({}, data_dict)
    else:
        ret = json.dumps({
            'message': _('Badly formatted data')
        })

    # response.headers['Content-Type'] = CONTENT_TYPES['json']
    return ret


def _sort_quick_links_items(quick_links_items):
    return sorted(carousel_items, key=lambda x: x.get('order'))


def _find_quick_links_item_by_id(quick_links_items, id):
    index = -1
    element = None
    for i, item in enumerate(quick_links_items):
        if item.get('id') == id:
            index = i
            element = item
            break
    return index, element


def _remove_file_by_path(path):
    '''
    :param path: something like /global/[uuid].png
    '''
    if path:
        existing_upload = GlobalUpload({
            'filename': path,
            'upload': None
        })
        existing_upload.delete()


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


hdx_quick_links.add_url_rule(u'/show', view_func=show)
hdx_quick_links.add_url_rule(u'/update', view_func=update, methods=[u'POST'])
hdx_quick_links.add_url_rule(u'/delete/<id>', view_func=delete, methods=[u'POST'])
