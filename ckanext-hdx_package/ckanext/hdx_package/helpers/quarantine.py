import ckan.model as model
import ckan.plugins.toolkit as tk

get_action = tk.get_action
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
abort = tk.abort
_ = tk._
c = tk.c

def resource_download_with_quarantine_check(self, id, resource_id, filename=None):

    context = {'model': model, 'session': model.Session,
               'user': c.user, 'auth_user_obj': c.userobj}

    try:
        resource_dict = get_action('resource_show')(context, {'id': resource_id})
        if resource_dict.get('in_quarantine'):
            raise NotAuthorized()
    except (NotFound, NotAuthorized):
        abort(404, _('Resource not found'))

