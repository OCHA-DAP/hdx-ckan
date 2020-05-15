from ckanext.hdx_search.controller_logic.search_logic import SearchLogic


class CustomPagesSearchLogic(SearchLogic):

    def _get_pager_function(self, package_type):
        def pager_url(q=None, page=None):
            params = list(self._params_nopage())
            params.append(('page', page))
            return self._search_url(params, package_type) + '#datasets-section'

        return pager_url
