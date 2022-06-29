from flask import Blueprint

import ckan.views.resource as resource_view
import ckanext.s3filestore.view as s3_resource_view
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckanext.hdx_package.helpers.analytics import resource_download_with_analytics
from ckanext.hdx_package.helpers.quarantine import resource_download_with_quarantine_check
from ckanext.hdx_theme.helpers.config import is_s3filestore_enabled

g = tk.g
get_action = tk.get_action
abort = tk.abort
_ = tk._
redirect = tk.redirect_to
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized

view = s3_resource_view if is_s3filestore_enabled() else resource_view
before_download_functions = [resource_download_with_quarantine_check, resource_download_with_analytics]

hdx_download_wrapper = Blueprint(u'hdx_download_wrapper', __name__)


def download(id, resource_id, filename=None):
    for f in before_download_functions:
        f(id, resource_id, filename)

    return view.download(id, resource_id, filename)


def download_at_position(id, n):
    context = {'model': model, 'session': model.Session, 'user': g.user, 'auth_user_obj': g.userobj}
    try:
        pkg_dict = get_action('package_show')(context, {'id': id})
        res_list = [r for r in pkg_dict.get('resources') if r.get('position') == n]
    except (NotFound, NotAuthorized):
        return abort(404, _('Resource not found'))
    except Exception as ex:
        return abort(404, _('Resource position not found'))
    if res_list:
        res = res_list[0]
        if res.get('url_type') == 'upload':
            return download(id, res.get('id'))
        else:
            return redirect(res.get('url'))
    return abort(404, _('Resource position not found'))


def download_resource_first(id):
    return download_at_position(id, 0)


hdx_download_wrapper.add_url_rule(u'/dataset/<id>/resource/<resource_id>/download', view_func=download)
hdx_download_wrapper.add_url_rule(u'/dataset/<id>/resource/<resource_id>/download/<filename>', view_func=download)

hdx_download_wrapper.add_url_rule(u'/dataset/<id>/resource_at_position/<int:n>/download',
                                  view_func=download_at_position)

hdx_download_wrapper.add_url_rule(u'/dataset/<id>/resource_first/download', view_func=download_resource_first)
