import ckan.model as model
import ckan.plugins.toolkit as tk

from ckanext.hdx_theme.controller_logic.ebola_search_logic import EbolaSearchLogic

get_action = tk.get_action
g = tk.g
config = tk.config


class EbolaReadLogic(object):
    flask_route_name = 'hdx_ebola.read'

    def __init__(self):
        super(EbolaReadLogic, self).__init__()
        self.redirect_result = None
        self.search_data = None

        self.cases_datastore_id = None

    def generate_dataset_results(self):
        search_logic = EbolaSearchLogic(self.flask_route_name).search().init_archived_url_helper()
        redirect_result = search_logic.redirect_if_needed()
        if redirect_result:
            self.redirect_result = redirect_result
            return None

        self.search_data = search_logic.template_data
        return self
