from collections import OrderedDict

import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.hdx_users.controller_logic.dashboard_search_logic import DashboardSearchLogic
from ckanext.hdx_package.helpers.freshness_calculator import UPDATE_STATUS_URL_FILTER

get_action = tk.get_action


class DashboardDatasetLogic(object):

    def __init__(self, userobj):
        super(DashboardDatasetLogic, self).__init__()
        self.userobj = userobj

        self.redirect_result = None
        self.user_dict = None
        self.search_data = None

    def read(self):
        self.user_dict = self._fetch_user_data()
        self.search_data = self._fetch_dataset_search_results()
        return self

    def _fetch_user_data(self):
        context = {'model': model, 'session': model.Session, 'for_view': True,
                   'user': self.userobj.name, 'auth_user_obj': self.userobj,
                   # Do NOT fetch the datasets we will fetch via package_search
                   'return_minimal': True,  # This is being deprecated
                   'include_num_followers': False,
                   'include_datasets': False
                   }
        data_dict = {'user_obj': self.userobj}

        return get_action('user_show')(context, data_dict)

    def _fetch_dataset_search_results(self):
        fq = 'maintainer:"{}"'.format(self.userobj.id)
        search_logic = DashboardSearchLogic()
        search_logic._search(additional_fq=fq, default_sort_by='due_date asc', ignore_capacity_check=True)
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
