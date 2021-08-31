import logging
from flask import Blueprint


import ckan.plugins.toolkit as tk
import ckan.plugins as plugins
import ckan.logic as logic

# from ckanext.hdx_theme.util.light_redirect import check_redirect_needed
from ckanext.hdx_dataviz.controller_logic.dataviz_search_logic import DatavizSearchLogic

get_action = tk.get_action
check_access = tk.check_access
render = tk.render
abort = tk.abort
log = logging.getLogger(__name__)
asbool = tk.asbool
h = tk.h

NotAuthorized = tk.NotAuthorized
NotFound = logic.NotFound

hdx_dataviz_gallery = Blueprint(u'hdx_dataviz_gallery', __name__, url_prefix=u'/dataviz-gallery')


def index():
    return _index('dataviz/index.html', True, False)


def _index(template_file, show_switch_to_desktop, show_switch_to_mobile):

    search_logic = DatavizSearchLogic()
    search_logic._search(additional_fq='in_dataviz_gallery:true', default_sort_by='metadata_modified', num_of_items=9)
    _populate_with_data_link(search_logic.template_data.page.items)
    template_data = {'data': search_logic.template_data}
    carousel_items = _fetch_carousel_items()
    carousel_items.sort(key=lambda item: item.get('priority'), reverse=True)
    _populate_with_data_link(carousel_items)
    _populate_with_after_show_data(carousel_items)
    template_data['data']['carousel_items'] = carousel_items

    return render(template_file, template_data)


def _fetch_carousel_items():
    result = get_action('package_search')({}, {
        'q': '',
        'fq': 'dataset_type:showcase extras_in_carousel_section:true',
        'rows': 5,
        'sort': 'metadata_modified desc'
    })
    return result['results']


def _populate_with_after_show_data(showcases):
    showcase_plugin = None
    for item in plugins.PluginImplementations(plugins.IPackageController):
        if item.name == 'showcase':
            showcase_plugin = item
    if showcases and showcase_plugin:
        for showcase in showcases:
            showcase_plugin.after_show({}, showcase)


def _populate_with_data_link(showcases):
    if showcases:
        for showcase in showcases:
            if not showcase.get('data_url'):
                showcase['data_url'] = h.url_for('showcase_blueprint.read', id=showcase['name'])

hdx_dataviz_gallery.add_url_rule(u'', view_func=index)
