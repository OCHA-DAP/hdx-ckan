import ckan.lib.helpers as h
import ckanext.hdx_search.controller_logic.search_logic as sl


class GroupSearchLogic(sl.SearchLogic):

    def __init__(self, id, flask_route_name):
        super(GroupSearchLogic, self).__init__()
        self.group_id = id
        self.flask_route_name = flask_route_name

        self.additional_fq = 'groups:"{}"'.format(self.group_id)

    def search(self):
        self._search(additional_fq=self.additional_fq)
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
        url = h.url_for(self.flask_route_name, id=self.group_id)
        return url
