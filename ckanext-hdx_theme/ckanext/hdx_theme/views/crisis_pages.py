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

hdx_crisis_pages = flask.Blueprint(u'hdx_crisis_pages', __name__)


def _prepare_crisis_page_lists(page_list):
    ongoing_list = []
    archived_list = []
    for page in page_list:
        if page.get('type') != 'event':
            continue
        item = {'id': page.get('id'), 'title': page.get('title'),
                'url': "/{page_type}/{page_name}".format(page_type=page.get('type'), page_name=page.get('name')),
                'modified': page.get('modified')}
        if page.get('status') == 'archived':
            archived_list.append(item)
        else:
            ongoing_list.append(item)

    ongoing_list.sort(key=lambda p: p.get('modified') or '', reverse=True)
    archived_list.sort(key=lambda p: p.get('modified') or '', reverse=True)

    return ongoing_list, archived_list


def show():
    context = {'model': model, 'session': model.Session,
               'user': g.user, 'auth_user_obj': g.userobj,
               'for_view': True, 'with_related': True}
    try:
        check_access('page_list', context, {})
    except Exception as ex:
        abort(404, 'Page not found')

    page_list = get_action('page_list')(context, {})
    ongoing_list, archived_list = _prepare_crisis_page_lists(page_list)

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
