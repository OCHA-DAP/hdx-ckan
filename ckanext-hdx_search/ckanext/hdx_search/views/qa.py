import logging

from flask import Blueprint

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckanext.hdx_search.controller_logic.qa_read_logic import QAReadLogic
from ckanext.hdx_search.controller_logic.qa_search_logic import QASearchLogic

g = tk.g
config = tk.config
request = tk.request
render = tk.render
redirect = tk.redirect_to
url_for = tk.url_for
get_action = tk.get_action
NotFound = tk.ObjectNotFound
check_access = tk.check_access
NotAuthorized = tk.NotAuthorized
abort = tk.abort
_ = tk._
h = tk.h

log = logging.getLogger(__name__)

hdx_qa = Blueprint(u'hdx_qa', __name__, url_prefix=u'/qa_dashboard')


def dashboard():
    qa_dashboard_enabled = config.get('hdx.qadashboard.enabled')
    if not qa_dashboard_enabled:
        abort(404, _('Page not found'))

    try:
        context = {'model': model, 'user': g.user,
                   'auth_user_obj': g.userobj}
        check_access('qa_dashboard_show', context)
    except (NotFound, NotAuthorized):
        abort(403, _('Not authorized to see this page'))

    search_logic = QASearchLogic().search().init_archived_url_helper()
    redirect_result = search_logic.redirect_if_needed()
    if redirect_result:
        return redirect_result

    read_logic = QAReadLogic().read()

    template_data = {
        'data': {
            'membership': read_logic.membership,
            'search_template_data': search_logic.template_data,
        },
    }

    return render('qa_dashboard/qa_dashboard.html', template_data)


hdx_qa.add_url_rule(u'/', view_func=dashboard, strict_slashes=False)
