import ckan.logic as logic
import ckan.model as model
from urlparse import parse_qs, urlparse
from ckan.common import _, c, g, request, response
import ckan.lib.helpers as h


def hdx_events_list():
    context = {'model': model, 'session': model.Session, 'user': c.user or c.author, 'auth_user_obj': c.userobj}

    events = logic.get_action('page_list')(context, {})
    archived = []
    ongoing = []
    for e in events:
        if e.get("type") == 'event':
            if e.get("status") == 'ongoing':
                ongoing.append(e)
            if e.get("status") == 'archived':
                archived.append(e)

    return {"archived": sorted(archived, key=lambda x: x['title']),
            "ongoing": sorted(ongoing, key=lambda x: x['title'])}


def _compute_iframe_style(section):
    style = 'width: 100%; '
    max_height = section.get('max_height')
    height = max_height if max_height else '400px'
    style += 'max-height: {}; '.format(max_height) if max_height else ''
    style += 'height: {}; '.format(height)
    section['style'] = style
    return section


def _find_dataset_filters(url):
    filters = parse_qs(urlparse(url).query)
    return filters


def generate_dataset_results(page_id, type, saved_filters):
    params_nopage = {
        k: v for k, v in request.params.items() if k != 'page'}

    mapping_name = _generate_action_name(type)

    def pager_url(q=None, page=None):
        params = params_nopage
        params['page'] = page
        url = h.url_for(mapping_name, id=page_id, **params) + '#datasets-section'
        return url

    fq = ''
    search_params = {}
    for key, values_list in saved_filters.items():
        if key == 'q':
            fq = '(text:({})) {}'.format(values_list[0], fq)
        elif key in _get_default_facet_titles().keys():
            for value in values_list:
                fq += '%s:"%s" ' % (key, value)
        elif key == 'fq':
            fq += '%s ' % (values_list[0],)
        elif key == 'sort':
            search_params['default_sort_by'] = values_list[0]
        elif key == 'ext_page_size':
            search_params['num_of_items'] = values_list[0]

    search_params['additional_fq'] = fq

    # package_type = 'dataset'
    # full_facet_info = self._search(package_type, pager_url, **search_params)
    #
    # c.other_links['current_page_url'] = h.url_for(mapping_name, id=page_id)

    return search_params


def _generate_action_name(type):
    return 'read_event' if type == 'event' else 'read_dashboards'


def _get_default_facet_titles():
    return {
        'organization': _('Organizations'),
        'groups': _('Groups'),
        # 'tags': _('Tags'),
        'vocab_Topics': _('Tags'),
        'res_format': _('Formats'),
        'license_id': _('Licenses'),
    }
