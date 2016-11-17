import ckan.logic as logic

import ckanext.hdx_pages.model as pages_model
import ckanext.hdx_pages.helpers.dictize as dictize

NotFound = logic.NotFound

@logic.side_effect_free
def page_show(context, data_dict):
    '''
    Fetch page from database
    :param id: the id or name of the page
    :type id: str
    :return: dictized page
    :rtype: dict
    '''

    page = pages_model.Page.get_by_id(id=data_dict['id'])
    if page is None:
        raise NotFound
    page_dict = dictize.page_dictize(page)
    logic.check_access('page_show', context, page_dict)

    return page_dict