import flask
import json
import logging
import uuid

from six import text_type

import ckan.plugins.toolkit as tk
import ckan.model as model

from ckan.types import Context
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

hdx_quick_links = flask.Blueprint(u'hdx_quick_links', __name__, url_prefix=u'/ckan-admin/quick-links')


def show():
    context = {u'user': g.user}
    try:
        check_access('hdx_quick_links_update', context, {})
    except tk.NotAuthorized:
        return abort(403, _('Not authorized to access this page'))

    action_context: Context = {'model': model, 'session': model.Session, 'user': g.user}
    setting_value = get_action('hdx_quick_links_settings_show')(action_context, {})
    template_data = {
        'data': {
            'hdx.quick_links.config': json.dumps(setting_value)
        }
    }

    return render('admin/quick_links.html', extra_vars=template_data)


def delete(id):
    context = {u'user': g.user}
    try:
        check_access('hdx_quick_links_update', context, {})
    except tk.NotAuthorized:
        return abort(403, _('Not authorized to access this page'))

    action_context: Context = {'model': model, 'session': model.Session, 'user': g.user}
    existing_setting_list = get_action('hdx_quick_links_settings_show')(action_context, {'not_initial': True})
    remove_index, remove_element = _find_quick_links_item_by_id(existing_setting_list, id)

    if remove_index >= 0:
        del existing_setting_list[remove_index]

    data_dict = {
        'hdx.quick_links.config': existing_setting_list
    }

    settings_json = get_action('hdx_quick_links_settings_update')(action_context, data_dict)

    return settings_json


def update():
    context = {u'user': g.user}
    try:
        check_access('hdx_quick_links_update', context, {})
    except tk.NotAuthorized:
        return abort(403, _('Not authorized to access this page'))

    item = _process_request()

    if item:
        action_context: Context = {'model': model, 'session': model.Session, 'user': g.user}
        existing_setting_list = get_action('hdx_quick_links_settings_show')(action_context, {'not_initial': True})

        if item.pop('new'):
            existing_setting_list.append(item)
        else:
            existing_index, existing_element = _find_quick_links_item_by_id(existing_setting_list, item.get('id'))
            existing_setting_list[existing_index] = item

        data_dict = {
            'hdx.quick_links.config': _sort_quick_links_items(existing_setting_list)
        }

        ret = get_action('hdx_quick_links_settings_update')(action_context, data_dict)
    else:
        ret = json.dumps({
            'message': _('Badly formatted data')
        })

    return ret


def _sort_quick_links_items(quick_links_items):
    return sorted(quick_links_items, key=lambda x: x.get('order'))


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

    title = request.form.get('title')
    if not title:
        return None
    else:
        item = {
            'title': title,
            # 'description': request.form.get('description'),
            # 'graphic': request.form.get('graphic'),
            # 'graphic_upload': request.form.get('graphic_upload'),
            'url': request.form.get('url'),
            'order': int(request.form.get('order', -1)),
            'newTab': True if request.form.get('newTab') == 'true' else False,
            'archived': True if request.form.get('archived') == 'true' else False,
            # 'embed': True if request.form.get('embed') == 'true' else False,
            'new': False if request.form.get('id') else True,
            'id': request.form.get('id') if request.form.get('id') else text_type(uuid.uuid4())
        }
        if request.form.get('buttonText'):
            item['buttonText'] = request.form.get('buttonText')

    return item


hdx_quick_links.add_url_rule(u'/show', view_func=show)
hdx_quick_links.add_url_rule(u'/update', view_func=update, methods=[u'POST'])
hdx_quick_links.add_url_rule(u'/delete/<id>', view_func=delete, methods=[u'POST'])
