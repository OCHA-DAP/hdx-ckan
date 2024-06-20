import ckan.lib.helpers as h

import ckanext.hdx_search.controller_logic.search_logic as sl


class CustomPagesSearchLogic(sl.SearchLogic):
    def __init__(self, id, type):
        super(CustomPagesSearchLogic, self).__init__()
        self.page_id = id
        self.type = type

    def _generate_action_name(self, type):
        return (
            "hdx_event.read_event"
            if type == "event"
            else "hdx_dashboard.read_dashboard"
        )

    def _search_url(self, params, package_type=None):
        """
        Returns the url of the current search type
        :param params: the parameters that will be added to the search url
        :type params: list of key-value tuples
        :param package_type: for now this is always 'dataset'
        :type package_type: string

        :rtype: string
        """
        url = self._current_url()
        return sl.url_with_params(url, params) + "#datasets-section"

    def _current_url(self):
        action_name = self._generate_action_name(self.type)
        url = h.url_for(action_name, id=self.page_id)
        return url
