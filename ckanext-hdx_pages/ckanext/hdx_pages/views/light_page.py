import json
import logging
from flask import Blueprint

import ckan.model as model
import ckan.plugins.toolkit as tk
import ckan.logic as logic

from ckan.common import _, config, g, request
import ckanext.hdx_pages.helpers.helper as page_h
# import ckanext.hdx_package.helpers.analytics as analytics
# import ckanext.hdx_package.helpers.custom_pages as cp_h
from ckanext.hdx_pages.controller_logic.custom_pages_search_logic import CustomPagesSearchLogic

from ckanext.hdx_theme.util.light_redirect import check_redirect_needed

get_action = tk.get_action
check_access = tk.check_access
render = tk.render
abort = tk.abort
log = logging.getLogger(__name__)

NotAuthorized = tk.NotAuthorized
NotFound = logic.NotFound

hdx_light_event = Blueprint(u'hdx_light_event', __name__, url_prefix=u'/m/event')
hdx_light_dashboard = Blueprint(u'hdx_light_dashboard', __name__, url_prefix=u'/m/dashboards')


@check_redirect_needed
def read_event(id):
    return _read(id, 'event', True, False)


@check_redirect_needed
def read_dashboard(id):
    return _read(id, 'dashboard', True, False)


def _read(id, type, show_switch_to_desktop, show_switch_to_mobile):
    try:
        context = {
            u'model': model,
            u'session': model.Session,
            u'user': g.user,
            u'auth_user_obj': g.userobj,
            u'for_view': True
        }
        check_access('site_read', context)
    except NotAuthorized:
        abort(403, _('Not authorized to see this page'))

    page_dict = None
    try:
        page_dict = get_action('page_show')(context, {'id': id})
    except NotAuthorized:
        abort(404, _('Page not found'))
    except NotFound:
        abort(404, _('Page not found'))

    _populate_template_data(page_dict)
    template_data = {
        'page_dict': page_dict,
        'page_has_desktop_version': show_switch_to_desktop,
        'page_has_mobile_version': show_switch_to_mobile,
    }

    return render(u'light/custom_pages/read.html', template_data)


def _populate_template_data(page_dict):
    if page_dict.get('sections'):
        sections = json.loads(page_dict['sections'])
        for section in sections:
            page_h._compute_iframe_style(section)
            if section.get('type', '') == 'data_list':
                saved_filters = page_h._find_dataset_filters(section.get('data_url', ''))
                package_type = 'dataset'
                cp_search_logic = CustomPagesSearchLogic(page_dict.get('name'), page_dict.get('type'))
                search_params = page_h.generate_dataset_results(page_dict.get('id'), page_dict.get('type'), saved_filters)
                cp_search_logic._search(package_type, **search_params)
                section['template_data'] = cp_search_logic.template_data
                log.info(saved_filters)
                # c.full_facet_info = self._generate_dataset_results(id, type, saved_filters)
            #
            #     # In case this is an AJAX request return JSON
            #     if self._is_facet_only_request():
            #         c.full_facet_info = self._generate_dataset_results(id, type, saved_filters)
            #         response.headers['Content-Type'] = CONTENT_TYPES['json']
            #         return json.dumps(c.full_facet_info)

        page_dict['sections'] = sections

        # if len(sections) > 0 and sections[0].get('type', '') == 'map':
        #     page_dict['title_section'] = sections[0]
        #     del sections[0]
    return page_dict


hdx_light_event.add_url_rule(u'/<id>', view_func=read_event)
hdx_light_dashboard.add_url_rule(u'/<id>', view_func=read_dashboard)
