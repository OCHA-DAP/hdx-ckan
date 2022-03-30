import logging

from flask import Blueprint

import ckan.lib.base as base
import ckan.plugins.toolkit as tk
from ckanext.hdx_users.controller_logic.dashboard_dataset_logic import DashboardDatasetLogic

log = logging.getLogger(__name__)

render = tk.render
get_action = tk.get_action
request = tk.request
g = tk.g
h = tk.h
_ = tk._
abort = base.abort
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized

hdx_user_dashboard = Blueprint(u'hdx_user_dashboard', __name__, url_prefix=u'/dashboard')


def datasets():
    """
    Dashboard tab for datasets. Modified to add the ability to change
    the order and ultimately filter datasets displayed
    """

    if not g.user:
        h.flash_error(_(u'Not authorized to see this page'))
        return h.redirect_to(u'home.index')

    dashboard_dataset_logic = DashboardDatasetLogic(g.userobj).read()
    if dashboard_dataset_logic.redirect_result:
        return dashboard_dataset_logic.redirect_result
    else:
        return render('user/dashboard_datasets.html', extra_vars={
            'user_dict': dashboard_dataset_logic.user_dict,
            'search_data': dashboard_dataset_logic.search_data
        })


hdx_user_dashboard.add_url_rule(u'/datasets', view_func=datasets)
