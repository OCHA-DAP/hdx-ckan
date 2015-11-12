import ckanext.hdx_pages.model as pages_model

def page_dictize(page):
    '''

    :param page:
    :type page: pages_model.Page
    :return:
    :rtype: dict
    '''

    return {
        'id': page.id,
        'name': page.name,
        'title': page.title,
        'description': page.description,
        'type': page.type,
        'sections': page.sections,
        'modified': page.modified.isoformat()
    }
