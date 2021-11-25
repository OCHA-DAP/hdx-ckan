import ckan.lib.helpers as h
import ckanext.hdx_search.controller_logic.search_logic as sl


class OrganizationSearchLogic(sl.SearchLogic):

    def __init__(self, name, flask_route_name, ignore_capacity_check=False):
        super(OrganizationSearchLogic, self).__init__()
        self.org_name = name
        self.flask_route_name = flask_route_name

        self.additional_fq = 'organization:"{}"'.format(self.org_name)
        self.ignore_capacity_check = ignore_capacity_check

    def search(self):
        self._search(additional_fq=self.additional_fq, ignore_capacity_check=self.ignore_capacity_check)
        return self

    def _search_url(self, params, package_type=None):
        '''
        Returns the url of the current search type
        :param params: the parameters that will be added to the search url
        :type params: list of key-value tuples
        :param package_type: for now this is always 'dataset'
        :type package_type: string

        :rtype: string
        '''
        # url = h.url_for(self._generate_action_name(self.type), id=self.org_id)
        suffix = '#datasets-section'
        url = self._current_url()
        return sl.url_with_params(url, params) + suffix

    def _current_url(self):
        url = h.url_for(self.flask_route_name, id=self.org_name)
        return url
