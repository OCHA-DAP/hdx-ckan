import logging

from decorator import decorator

import ckan.plugins.toolkit as tk

abort = tk.abort
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
_ = tk._

log = logging.getLogger(__name__)


@decorator
def catch_http_exceptions(original_action, *args, **kw):
    try:
        return original_action(*args, **kw)
    except (NotFound, NotAuthorized):
        return abort(404, _(u'Page not found'))


class FlaskEmailFilter(logging.Filter):
    def filter(self, log_record):
        try:
            if log_record.msg.code == 404:
                # don't send emails for pages/objects that were not found
                return False
        except AttributeError as e:
            pass
        return True
