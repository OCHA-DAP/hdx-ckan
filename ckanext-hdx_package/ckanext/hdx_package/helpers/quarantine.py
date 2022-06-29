import ckan.model as model
import ckan.plugins.toolkit as tk

get_action = tk.get_action
check_access = tk.check_access
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
abort = tk.abort
_ = tk._
g = tk.g


def resource_download_with_quarantine_check(id, resource_id, filename=None):

    context = {'model': model, 'session': model.Session,
               'user': g.user, 'auth_user_obj': g.userobj}

    try:
        resource_dict = get_action('resource_show')(context, {'id': resource_id})
        check_access('hdx_resource_download', context, resource_dict)
    except (NotFound, NotAuthorized):
        return abort(404, _('Resource not found'))

