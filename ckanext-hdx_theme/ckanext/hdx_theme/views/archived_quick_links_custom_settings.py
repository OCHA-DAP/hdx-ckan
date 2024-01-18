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


def _prepare_archived_page_list(page_list):
    res = []
    for page in page_list:
        if page.get('status') == 'archived':
            item= {'id': page.get('id'), 'title': page.get('title'),
                   'url': "/{page_type}/{page_name}".format(page_type=page.get('type'), page_name=page.get('name'))}
            res.append(item)
    return res

def _prepare_archived_viz_list(viz_list):
    res = []
    for viz in viz_list:
        if viz.get('archived', False):
            item= {'id': viz.get('id'), 'title': viz.get('title'),
                   'url': viz.get('url')}
            res.append(item)
    return res

def show():
    context = {'model': model, 'session': model.Session,
               'user': g.user, 'auth_user_obj': g.userobj,
               'for_view': True, 'with_related': True}
    try:
        check_access('page_list', context, {})
    except Exception as ex:
        abort(404, 'Page not found')

    archived_items_list = []

    # context = {u'user': g.user}
    # check_access('hdx_quick_links_update', context, {})
    viz_list = get_action('hdx_quick_links_settings_show')({}, {})
    archived_viz_list = _prepare_archived_viz_list(viz_list)
    archived_items_list.extend(archived_viz_list)

    page_list = get_action('page_list')(context, {})
    archived_page_list = _prepare_archived_page_list(page_list)

    archived_items_list.extend(archived_page_list)

    template_data = {
        'data': {
            'viz_list': archived_items_list
        },
        'errors': '',
        'error_summary': '',
    }

    return render('archived_quick_links/main.html', extra_vars=template_data)


hdx_archived_quick_links.add_url_rule(u'/archive', view_func=show)
