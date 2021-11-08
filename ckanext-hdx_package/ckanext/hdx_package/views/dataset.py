from flask import Blueprint

import ckan.plugins.toolkit as tk

import ckan.logic as logic

from ckanext.hdx_package.views.light_dataset import generic_search
from ckanext.hdx_search.controller_logic.qa_logs_logic import QALogsLogic
from ckanext.hdx_theme.util.light_redirect import check_redirect_needed

get_action = tk.get_action
check_access = tk.check_access
request = tk.request
render = tk.render
abort = tk.abort
redirect = tk.redirect_to
_ = tk._

NotAuthorized = tk.NotAuthorized
NotFound = logic.NotFound

hdx_dataset = Blueprint(u'hdx_dataset', __name__, url_prefix=u'/dataset')
hdx_search = Blueprint(u'hdx_search', __name__, url_prefix=u'/search')


@check_redirect_needed
def search():
    return generic_search(u'search/search.html')


def qa_pii_log(id, resource_id, file_name):
    qa_logs_logic = QALogsLogic(resource_id, file_name).read()

    if request.args.get("noredirect"):
        return qa_logs_logic.url
    else:
        return redirect(qa_logs_logic.url)


def qa_sdcmicro_log(id, resource_id):
    qa_logs_logic = QALogsLogic(resource_id, 'sdc.log.txt').read()
    return redirect(qa_logs_logic.url)


hdx_search.add_url_rule(u'', view_func=search)
hdx_dataset.add_url_rule(u'', view_func=search)
hdx_dataset.add_url_rule(u'<id>/resource/<resource_id>/qa_sdcmicro_log', view_func=qa_sdcmicro_log)
hdx_dataset.add_url_rule(u'<id>/resource/<resource_id>/qa_pii_log/<file_name>', view_func=qa_pii_log)
