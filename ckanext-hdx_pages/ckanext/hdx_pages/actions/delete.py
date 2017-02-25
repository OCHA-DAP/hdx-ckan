import ckanext.hdx_pages.model as pages_model
import ckanext.hdx_pages.helpers.dictize as dictize
import ckan.logic as logic

NotFound = logic.NotFound


def page_delete(context, data_dict):
    '''
    Delete a meta information entry
    :param id: the id or name of the page
    :type id: str
    :return: deleted dictized page
    :rtype: dict
    '''

    logic.check_access('page_delete', context, data_dict)

    model = context['model']
    page = pages_model.Page.get_by_id(id=data_dict['id'])
    if page is None:
        raise NotFound
    page.delete()
    model.repo.commit()
    return dictize.page_dictize(page)


