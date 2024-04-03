import logging

from flask import Blueprint

import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

# shortcuts
h = tk.h
get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
ValidationError = tk.ValidationError
clean_dict = logic.clean_dict
tuplize_dict = logic.tuplize_dict
parse_params = logic.parse_params
redirect = h.redirect_to
url_for = tk.url_for
check_access = tk.check_access
abort = tk.abort
render = tk.render
g = tk.g
_ = tk._
request = tk.request

hdx_org_join = Blueprint(u'hdx_org_join', __name__, url_prefix=u'/org/join')


def org_join() -> str:
    return redirect(url_for('hdx_org_join.find_organisation'))


def find_organisation() -> str:
    context = {
        'model': model,
        'session': model.Session
    }

    template_data = {}
    return render('onboarding/org-join/find-organisation.html', extra_vars=template_data)


hdx_org_join.add_url_rule(u'/', view_func=org_join, strict_slashes=False)
hdx_org_join.add_url_rule(u'/find/', view_func=find_organisation, methods=[u'GET'], strict_slashes=False)
