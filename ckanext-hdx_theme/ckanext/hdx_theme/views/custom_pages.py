import logging
import flask
import ckan.model as model
import ckan.plugins.toolkit as tk

abort = tk.abort
g = tk.g
check_access = tk.check_access
get_action = tk.get_action
render = tk.render

log = logging.getLogger(__name__)

hdx_custom_pages = flask.Blueprint(u'hdx_custom_pages', __name__, url_prefix=u'/ckan-admin/pages')


def index():
    context = {'model': model, 'session': model.Session,
               'user': g.user, 'auth_user_obj': g.userobj,
               'for_view': True, 'with_related': True}

    try:
        check_access('admin_page_list', context, {})
    except Exception as ex:
        abort(404, 'Page not found')

    page_list = get_action('admin_page_list')(context, {})

    template_data = {
        'page_list': page_list
    }

    return render('admin/pages.html', extra_vars=template_data)


hdx_custom_pages.add_url_rule(u'/show', view_func=index)
