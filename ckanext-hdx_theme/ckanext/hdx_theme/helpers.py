import ckan.lib.helpers as h

downloadable_formats = {
    'csv', 'xls', 'txt', 'jpg', 'jpeg', 'png', 'gif', 'zip', 'xml'
}

def is_downloadable(resource):
    format = resource.get('format', 'data').lower()
    if format in downloadable_formats:
        return True
    return False

def get_facet_items_dict(facet, limit=10, exclude_active=False):
    facets = h.get_facet_items_dict(facet, exclude_active=exclude_active)
    no_items = facets.__len__();
    if limit:
        return (facets[:limit],no_items)
    else:
        return (facets,no_items)
    
    
