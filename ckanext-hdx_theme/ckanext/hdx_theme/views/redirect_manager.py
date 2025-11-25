import logging
import flask
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
from ckan.common import current_user

abort = tk.abort
g = tk.g
check_access = tk.check_access
get_action = tk.get_action
render = tk.render
redirect = tk.redirect_to
config = tk.config

log = logging.getLogger(__name__)

hdx_redirect_manager = flask.Blueprint(u'hdx_redirect_manager', __name__, url_prefix=u'/redirect-manager')

def redirect_page(page_name):
    if not current_user.is_authenticated:
        abort(404)

    if page_name == 'api_tokens_management':
        redirect_url = h.url_for('user.api_tokens', id=current_user.name)
        return redirect(redirect_url)
    else:
        abort(404)

hdx_redirect_manager.add_url_rule(u'/<page_name>/', view_func=redirect_page, strict_slashes=False)
