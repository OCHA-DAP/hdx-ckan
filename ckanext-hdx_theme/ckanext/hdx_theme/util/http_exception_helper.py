from decorator import decorator

import ckan.plugins.toolkit as tk

abort = tk.abort
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
_ = tk._


@decorator
def catch_http_exceptions(original_action, *args, **kw):
    try:
        original_action(*args, **kw)
    except (NotFound, NotAuthorized):
        return abort(404, _(u'Page not found'))
