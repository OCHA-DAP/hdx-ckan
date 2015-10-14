import logging

import ckan.logic as logic
import ckan.model as model



log = logging.getLogger(__name__)


get_action = logic.get_action
_check_access = logic.check_access

def populate_related_items_count(context, data_dict):
    pkg_dict_list = data_dict.get('pkg_dict_list', {})
    for pkg_dict in pkg_dict_list:
    	pkg = model.Package.get(pkg_dict['id'])
        _check_access('package_show',context, pkg_dict)
        rel_items = get_action('related_list')(context, {'id': pkg_dict['id']})
        pkg_dict['related_count'] = len(rel_items)
    return pkg_dict_list