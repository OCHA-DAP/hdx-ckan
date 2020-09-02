import ckan.lib.helpers as h
import ckanext.hdx_search.controller_logic.search_logic as sl


class GroupSearchLogic(sl.SearchLogic):

    def __init__(self, id):
        super(GroupSearchLogic, self).__init__()
        self.group_id = id

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
        url = h.url_for('hdx_light_group.light_read', id=self.group_id)
        return sl.url_with_params(url, params) + suffix
