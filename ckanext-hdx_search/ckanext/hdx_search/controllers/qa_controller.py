import logging
from urllib import urlencode
import sqlalchemy
from pylons import config

import ckan.lib.base as base
import ckan.lib.helpers as h
import ckan.lib.navl.dictization_functions as dict_fns
import ckan.logic as logic
import ckan.model as model

import ckanext.hdx_search.helpers.search_history as search_history

from ckan.common import OrderedDict, _, json, request, c, response

from ckan.controllers.api import CONTENT_TYPES

from ckanext.hdx_search.controllers.search_controller import HDXSearchController

_validate = dict_fns.validate
_check_access = logic.check_access

_select = sqlalchemy.sql.select
_aliased = sqlalchemy.orm.aliased
_or_ = sqlalchemy.or_
_and_ = sqlalchemy.and_
_func = sqlalchemy.func
_desc = sqlalchemy.desc
_case = sqlalchemy.case
_text = sqlalchemy.text

log = logging.getLogger(__name__)

render = base.render
abort = base.abort
redirect = h.redirect_to

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
check_access = logic.check_access
get_action = logic.get_action

NUM_OF_ITEMS = 25


def _encode_params(params):
    return [(k, v.encode('utf-8') if isinstance(v, basestring) else str(v))
            for k, v in params]


class HDXQAController(HDXSearchController):
    def search(self):
        try:
            context = {'model': model, 'user': c.user or c.author,
                       'auth_user_obj': c.userobj}
            check_access('qa_dashboard_show', context)
        except (NotFound, NotAuthorized):
            abort(404, _('Not authorized to see this page'))

        package_type = 'dataset'

        params_nopage = self._params_nopage()
        c.search_url_params = urlencode(_encode_params(params_nopage))

        def pager_url(q=None, page=None):
            params = list(params_nopage)
            params.append(('page', page))
            url = h.url_for('qa_dashboard')
            params = _encode_params(params)
            return url + u'?' + urlencode(params)

        c.full_facet_info = self._search(package_type, pager_url, use_solr_collapse=True)

        c.cps_off = config.get('hdx.cps.off', 'false')
        c.other_links['current_page_url'] = h.url_for('qa_dashboard')
        query_string = request.params.get('q', u'')
        if c.userobj and query_string:
            search_history.store_search(query_string, c.userobj.id)

        # If we're only interested in the facet numbers a json will be returned with the numbers
        if self._is_facet_only_request():
            response.headers['Content-Type'] = CONTENT_TYPES['json']
            return json.dumps(c.full_facet_info)
        else:
            self._setup_template_variables(context, {},
                                           package_type=package_type)
            return self._search_template()

    def _search_template(self):
        return render('qa_dashboard/qa_dashboard.html')
