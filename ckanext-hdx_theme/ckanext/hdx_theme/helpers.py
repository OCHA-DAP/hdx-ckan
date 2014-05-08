import ckan.lib.helpers as h
from ckan.common import (
     c, request
)
import ckan.model as model


downloadable_formats = {
    'csv', 'xls', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'xml'
}

def is_downloadable(resource):
    format = resource.get('format', 'data').lower()
    if format in downloadable_formats:
        return True
    return False

def get_facet_items_dict(facet, limit=10, exclude_active=False):
    facets = h.get_facet_items_dict(facet, limit, exclude_active=exclude_active)
    no_items = c.search_facets.get(facet)['items'].__len__()
    
    if c.search_facets_limits:
        limit = c.search_facets_limits.get(facet)
    if limit:
        return (facets[:limit],no_items)
    else:
        return (facets,no_items)
    
    

def get_last_modifier_user(package_id):
    pkg_list  = model.Session.query(model.Package).filter(model.Package.id == package_id).all()
    pkg = pkg_list[0]
    rev_id = pkg.latest_related_revision.id
    act_list = model.Session.query(model.Activity).filter(model.Activity.revision_id == rev_id).all()
    act = act_list[0]
    usr_id = act.user_id
    return model.User.get(usr_id)

def get_filtered_params_list(params):
    result = []
    for (key, value) in params.items():
        if key not in {'q','sort'} :
            result.append((key,value))
    return result;
    