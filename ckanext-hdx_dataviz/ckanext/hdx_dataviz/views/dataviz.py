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
    search_logic._search(default_sort_by='metadata_modified')
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


def __generate_sample_index_data():
    template_data = {
        'data': {
            'total_items': 10,
            'full_facet_info': {
                'num_of_selected_filters': 1,
                'filters_selected': True
            }
        },
        'errors': '',
        'error_summary': '',
    }
    template_data['data']['page'] = h.Page(collection=[
        {
            'id': 1,
            'title': 'Displaced in Yemen',
            'description': 'A jouney of 426 kilometers in search of safety: Almost six years of conflict have left 80 percent of Yemen\'s population, over 24 million people have (more text more text more text more text more text more text more text more text )',
            'date': '1 Dec 2020',
            'label': 'Yemen',
            'org': {
                'name': 'HDX',
                'url': 'https://data.humdata.local/org/hdx'
            },
            'image': 'https://data.humdata.org/uploads/showcase/2020-03-31-094347.151256covid-19-map-2020-03-31.png'
        },
        {
            'id': 2,
            'title': 'Cambodia - 4W Flood Response',
            'description': 'A jouney of 426 kilometers in search of safety: Almost six years of conflict have left 80 percent of Yemen\'s population, over 24 million people have (more text more text more text more text more text more text more text more text )',
            'date': '1 Dec 2020',
            'label': 'Cambodia',
            'org': {
                'name': 'HDX',
                'url': 'https://data.humdata.local/org/hdx'
            },
            'image': 'https://reliefweb.int/sites/reliefweb.int/files/styles/location-image/public/country-location-images/pse.png'
        },
        {
            'id': 1,
            'title': 'Displaced in Yemen',
            'description': 'A jouney of 426 kilometers in search of safety: Almost six years of conflict have left 80 percent of Yemen\'s population, over 24 million people have (more text more text more text more text more text more text more text more text )',
            'date': '1 Dec 2020',
            'label': 'Yemen',
            'org': {
                'name': 'HDX',
                'url': 'https://data.humdata.local/org/hdx'
            },
            'image': 'https://data.humdata.org/uploads/showcase/2020-03-31-094347.151256covid-19-map-2020-03-31.png'
        },
        {
            'id': 2,
            'title': 'Cambodia - 4W Flood Response',
            'description': 'A jouney of 426 kilometers in search of safety: Almost six years of conflict have left 80 percent of Yemen\'s population, over 24 million people have (more text more text more text more text more text more text more text more text )',
            'date': '1 Dec 2020',
            'label': 'Cambodia',
            'org': {
                'name': 'HDX',
                'url': 'https://data.humdata.local/org/hdx'
            },
            'image': 'https://reliefweb.int/sites/reliefweb.int/files/styles/location-image/public/country-location-images/swe.png'
        },
        {
            'id': 1,
            'title': 'Displaced in Yemen',
            'description': 'A jouney of 426 kilometers in search of safety: Almost six years of conflict have left 80 percent of Yemen\'s population, over 24 million people have (more text more text more text more text more text more text more text more text )',
            'date': '1 Dec 2020',
            'label': 'Yemen',
            'org': {
                'name': 'HDX',
                'url': 'https://data.humdata.local/org/hdx'
            },
            'image': 'https://data.humdata.org/uploads/showcase/2020-03-31-094347.151256covid-19-map-2020-03-31.png'
        },
        {
            'id': 2,
            'title': 'Cambodia - 4W Flood Response',
            'description': 'A jouney of 426 kilometers in search of safety: Almost six years of conflict have left 80 percent of Yemen\'s population, over 24 million people have (more text more text more text more text more text more text more text more text )',
            'date': '1 Dec 2020',
            'label': 'Cambodia',
            'org': {
                'name': 'HDX',
                'url': 'https://data.humdata.local/org/hdx'
            },
            'image': 'https://reliefweb.int/sites/reliefweb.int/files/styles/location-image/public/country-location-images/pse.png'
        },
        {
            'id': 1,
            'title': 'Displaced in Yemen',
            'description': 'A jouney of 426 kilometers in search of safety: Almost six years of conflict have left 80 percent of Yemen\'s population, over 24 million people have (more text more text more text more text more text more text more text more text )',
            'date': '1 Dec 2020',
            'label': 'Yemen',
            'org': {
                'name': 'HDX',
                'url': 'https://data.humdata.local/org/hdx'
            },
            'image': 'https://data.humdata.local/org/hdx'
        },
        {
            'id': 2,
            'title': 'Cambodia - 4W Flood Response',
            'description': 'A jouney of 426 kilometers in search of safety: Almost six years of conflict have left 80 percent of Yemen\'s population, over 24 million people have (more text more text more text more text more text more text more text more text )',
            'date': '1 Dec 2020',
            'label': 'Cambodia',
            'org': {
                'name': 'HDX',
                'url': 'https://data.humdata.local/org/hdx'
            },
            'image': 'https://data.humdata.local/org/hdx'
        },
    ])
    return template_data


hdx_dataviz_gallery.add_url_rule(u'', view_func=index)
