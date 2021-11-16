import flask
import logging

import ckan.model as model
import ckan.plugins.toolkit as tk

abort = tk.abort
_ = tk._
g = tk.g
h = tk.h
request = tk.request
check_access = tk.check_access
get_action = tk.get_action
render = tk.render

log = logging.getLogger(__name__)

hdx_archived_quick_links = flask.Blueprint(u'hdx_archived_quick_links', __name__)


def _prepare_pages(page_list):
    res = []
    for page in page_list:
        if page.get('status') == 'archived':
            res.append(page)
    return res


def show():
    context = {'model': model, 'session': model.Session,
               'user': g.user, 'auth_user_obj': g.userobj,
               'for_view': True, 'with_related': True}
    try:
        check_access('page_list', context, {})
    except Exception as ex:
        abort(404, 'Page not found')

    page_list = get_action('page_list')(context, {})
    _pages = _prepare_pages(page_list)

    template_data = {
        'data': {
            'pages': _pages
        },
        'errors': '',
        'error_summary': '',
    }

    return render('archived_quick_links/main.html', extra_vars=template_data)


hdx_archived_quick_links.add_url_rule(u'/archive', view_func=show)
