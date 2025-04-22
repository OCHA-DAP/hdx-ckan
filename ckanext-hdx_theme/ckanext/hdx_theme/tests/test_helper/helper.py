import ckan.plugins.toolkit as tk

h = tk.h

def _getPackagePageByBlueprint(app, blueprint, package_id, apitoken=None):
    page = None
    url = h.url_for(blueprint, id=package_id)
    if apitoken:
        page = app.get(url, headers={'Authorization': apitoken})
    else:
        page = app.get(url)
    return page
