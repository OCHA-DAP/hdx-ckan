import ckan.lib.helpers as h
from ckan.common import (
     c, request
)

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
    if limit:
        return (facets[:limit],no_items)
    else:
        return (facets,no_items)
    
    
