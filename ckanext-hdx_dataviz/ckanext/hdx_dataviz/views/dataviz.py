import logging
from flask import Blueprint

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.logic as logic
import ckan.views.dataset as dataset

from ckan.common import _, config, g, request

from ckanext.hdx_theme.util.light_redirect import check_redirect_needed

get_action = tk.get_action
check_access = tk.check_access
render = tk.render
abort = tk.abort
log = logging.getLogger(__name__)

NotAuthorized = tk.NotAuthorized
NotFound = logic.NotFound

hdx_dataviz_gallery = Blueprint(u'hdx_dataviz_gallery', __name__, url_prefix=u'/dataviz-gallery')


@check_redirect_needed
def index():
    return _index('dataviz/index.html', True, False)


@check_redirect_needed
def read_dataviz(id):
    # return _read(id, 'event', True, False)
    pass


def _index(template_file, show_switch_to_desktop, show_switch_to_mobile):
    # context = {
    #     'model': model,
    #     'session': model.Session,
    #     'for_view': True,
    #     'with_private': False
    # }
    # try:
    #     check_access('site_read', context)
    # except NotAuthorized:
    #     abort(403, _('Not authorized to see this page'))
    #
    # try:
    #     q = request.params.get('q', '')
    #     page = int(request.params.get('page', 1))
    #     limit = int(request.params.get('limit', 25))
    #     sort_option = request.params.get('sort', 'title asc')
    # except ValueError:
    #     abort(404, 'Page not found')
    #     sort_option = ''
    #     q = ''
    #
    # template_data = {
    #     'q': q,
    #     'sorting_selected': sort_option,
    #     'limit_selected': limit,
    #     'page': page,
    #     'page_has_desktop_version': show_switch_to_desktop,
    #     'page_has_mobile_version': show_switch_to_mobile,
    # }

    template_data = {
        'data': {
            'total_items': 10,
            'full_facet_info': {
                'num_of_selected_filters': 1,
                'filters_selected': True
            },
            'page': [
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
            ]
        },
        'errors': '',
        'error_summary': '',
    }

    return render(template_file, template_data)

    # return dataset.search('showcase')


hdx_dataviz_gallery.add_url_rule(u'', view_func=index)
hdx_dataviz_gallery.add_url_rule(u'/<id>', view_func=read_dataviz)
