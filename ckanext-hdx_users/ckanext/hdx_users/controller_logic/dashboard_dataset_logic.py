from collections import OrderedDict

from ckanext.hdx_users.controller_logic.dashboard_search_logic import DashboardSearchLogic
from ckanext.hdx_package.helpers.freshness_calculator import UPDATE_STATUS_URL_FILTER
from ckanext.hdx_search.helpers.constants import DEFAULT_SORTING


class DashboardDatasetLogic(object):

    def __init__(self, user_dict, owner_view):
        super(DashboardDatasetLogic, self).__init__()
        self.user_dict = user_dict
        self.owner_view = owner_view

        self.redirect_result = None
        self.search_data = None

    def read(self):
        self.search_data = self._fetch_dataset_search_results()
        return self

    def _fetch_dataset_search_results(self):
        fq = 'maintainer:"{}"'.format(self.user_dict['id'])
        search_logic = DashboardSearchLogic(self.user_dict['name'], self.owner_view)
        default_sort_by = 'due_date asc' if self.owner_view else DEFAULT_SORTING
        search_logic._search(additional_fq=fq, default_sort_by=default_sort_by, ignore_capacity_check=True)
        archived_url_helper = search_logic.add_archived_url_helper()
        redirect_result = archived_url_helper.redirect_if_needed()
        if redirect_result:
            self.redirect_result = redirect_result
            return None
        full_facet_info = search_logic.template_data.get('full_facet_info', {})
        old_facets = full_facet_info.get('facets')
        if UPDATE_STATUS_URL_FILTER in old_facets:
            new_facets = OrderedDict()
            new_facets[UPDATE_STATUS_URL_FILTER] = old_facets[UPDATE_STATUS_URL_FILTER]
            new_facets.update(old_facets)
            full_facet_info['facets'] = new_facets
        return search_logic.template_data
