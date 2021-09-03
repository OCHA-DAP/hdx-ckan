import ckan.lib.helpers as h
import ckanext.hdx_search.controller_logic.search_logic as sl


class DatavizSearchLogic(sl.SearchLogic):

    def __init__(self):
        super(DatavizSearchLogic, self).__init__(package_type='showcase')

    def _search_url(self, params, package_type=None):
        url = h.url_for('hdx_dataviz_gallery.index')
        return sl.url_with_params(url, params)
