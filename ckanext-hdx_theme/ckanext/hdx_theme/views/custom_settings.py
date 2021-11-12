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

hdx_carousel = flask.Blueprint(u'hdx_carousel', __name__, url_prefix=u'/ckan-admin/carousel')


def show():
    context = {u'user': g.user}
    check_access('hdx_carousel_update', context, {})

    setting_value = get_action('hdx_carousel_settings_show')({}, {})
    template_data = {
        'data': {
            'hdx.carousel.config': json.dumps(setting_value)
        }
    }

    return render('admin/carousel.html', extra_vars=template_data)


def delete(id):
    context = {u'user': g.user}
    check_access('hdx_carousel_update', context, {})
    # delete_id = request.params.get('id')
    existing_setting_list = get_action('hdx_carousel_settings_show')({'not_initial': True}, {})
    remove_index, remove_element = _find_carousel_item_by_id(existing_setting_list, id)

    if remove_index >= 0:
        del existing_setting_list[remove_index]

    if remove_element:
        _remove_file_by_path(remove_element.get('graphic'))

    data_dict = {
        'hdx.carousel.config': existing_setting_list
    }

    settings_json = get_action('hdx_carousel_settings_update')({}, data_dict)

    # response.headers['Content-Type'] = CONTENT_TYPES['json']
    return settings_json


def update():
    context = {u'user': g.user}
    check_access('hdx_carousel_update', context, {})

    item = _process_request()

    if item:
        existing_setting_list = get_action('hdx_carousel_settings_show')({'not_initial': True}, {})
        _persist_file(item)

        if item.pop('new'):
            existing_setting_list.append(item)
        else:
            existing_index, existing_element = _find_carousel_item_by_id(existing_setting_list, item.get('id'))
            existing_setting_list[existing_index] = item

        data_dict = {
            'hdx.carousel.config': _sort_carousel_items(existing_setting_list)
        }

        ret = get_action('hdx_carousel_settings_update')({}, data_dict)
    else:
        ret = json.dumps({
            'message': _('Badly formatted data')
        })

    # response.headers['Content-Type'] = CONTENT_TYPES['json']
    return ret


def _sort_carousel_items(carousel_items):
    return sorted(carousel_items, key=lambda x: x.get('order'))


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


def _persist_file(item):
    # For some reason FieldStorage has the boolean value of false so we compare to None
    graphic_upload = item.get('graphic_upload')
    if graphic_upload is not None and graphic_upload != 'undefined':
        # remove previous file if exists
        _remove_file_by_path(item.get('graphic'))

        upload = GlobalUpload({
            'filename': '{}_{}'.format(item.get('id')[0:4], text_type(uuid.uuid4())),
            'upload': graphic_upload
        })
        upload.upload()
        item['graphic'] = h.url_for('hdx_global_file_server.global_file_download', filename=upload.filename)
        del item['graphic_upload']


def _process_request():
    '''
    :return: processes the request and returns a carousel item
    :rtype: dict
    '''

    title = request.form.get('title')
    if not title:
        return None
    else:
        item = {
            'title': title,
            'description': request.form.get('description'),
            'graphic': request.form.get('graphic'),
            'graphic_upload': request.files.get('graphic_upload'),
            'url': request.form.get('url'),
            'order': int(request.form.get('order', -1)),
            'newTab': True if request.form.get('newTab') == 'true' else False,
            'embed': True if request.form.get('embed') == 'true' else False,
            'new': False if request.form.get('id') else True,
            'id': request.form.get('id') if request.form.get('id') else text_type(uuid.uuid4())
        }
        if request.form.get('buttonText'):
            item['buttonText'] = request.form.get('buttonText')

    return item


hdx_carousel.add_url_rule(u'/show', view_func=show)
hdx_carousel.add_url_rule(u'/update', view_func=update, methods=[u'POST'])
hdx_carousel.add_url_rule(u'/delete/<id>', view_func=delete, methods=[u'POST'])
