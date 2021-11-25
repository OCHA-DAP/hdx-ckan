from flask import Blueprint

import ckan.plugins.toolkit as tk
from ckanext.hdx_theme.controller_logic.ebola_read_logic import EbolaReadLogic

render = tk.render
config = tk.config

hdx_ebola = Blueprint(u'hdx_ebola', __name__, url_prefix=u'/ebola')


def read():
    read_logic = EbolaReadLogic().generate_dataset_results()
    template_data = {
        'data': {
            # 'top_line_items': top_line_items,
            'cases_datastore_id': config.get('hdx.ebola.datastore.cases'),
            'search_data': read_logic.search_data,
        },
        'errors': None,
        'error_summary': None,
    }
    return render('crisis/crisis-ebola.html', template_data)


hdx_ebola.add_url_rule(u'', view_func=read)
