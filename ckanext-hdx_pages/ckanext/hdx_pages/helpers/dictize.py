import ckanext.hdx_pages.model as pages_model
import json


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
        'keywords': page.description,
        'type': page.type,
        'state': page.state,
        'status': page.status,
        'sections': page.sections,
        'extras': json.loads(page.extras) if page.extras else None,
        'modified': page.modified.isoformat()
    }
