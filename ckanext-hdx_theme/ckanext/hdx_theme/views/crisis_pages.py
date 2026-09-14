import flask
import logging

import ckan.plugins.toolkit as tk

get_action = tk.get_action
render = tk.render

log = logging.getLogger(__name__)

hdx_crisis_pages = flask.Blueprint(u'hdx_crisis_pages', __name__)

_CRISIS_URL_PREFIXES = ('/event', '/m/event')


def _prepare_crisis_page_lists(quick_links):
    ongoing_list = []
    archived_list = []
    for link in quick_links:
        url = link.get('url') or ''
        if not url.lower().startswith(_CRISIS_URL_PREFIXES):
            continue
        item = {'id': link.get('id'), 'title': (link.get('title') or '').strip(),
                'url': url, 'order': link.get('order', 0)}
        if link.get('archived', False):
            archived_list.append(item)
        else:
            ongoing_list.append(item)

    ongoing_list.sort(key=lambda p: p.get('order') or 0)
    archived_list.sort(key=lambda p: p.get('order') or 0)

    return ongoing_list, archived_list


def show():
    quick_links = get_action('hdx_quick_links_settings_show')({}, {})
    ongoing_list, archived_list = _prepare_crisis_page_lists(quick_links)

    template_data = {
        'data': {
            'ongoing_list': ongoing_list,
            'archived_list': archived_list,
        },
        'errors': '',
        'error_summary': '',
    }

    return render('crisis_pages/main.html', extra_vars=template_data)


hdx_crisis_pages.add_url_rule(u'/crisis-pages', view_func=show)
