import ckan.logic as logic
from ckan.model import meta
import ckanext.hdx_pages.model as pages_model
import ckanext.hdx_pages.helpers.dictize as dictize
from ckanext.hdx_pages.model import PageGroupAssociation, PageTagAssociation
from ckan.common import _

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
    logic.check_access('page_show', context, data_dict)
    id = data_dict.get('id')
    if not id:
        raise logic.ValidationError({'id': _('Missing value')})
    page = pages_model.Page.get_by_id(id=id)
    if page is None:
        raise NotFound
    page_dict = dictize.page_dictize(page)
    page_dict['tags'] = _process_tags(page, context)
    # logic.check_access('page_show', context, page_dict)

    return page_dict


def _process_tags(page, context):
    result = []
    for pt in page.tags_assoc_all:
        tag = logic.get_action('tag_show')(context, {'id': pt.tag_id})
        result.append(tag)
    return result


@logic.side_effect_free
def page_group_list(context, data_dict):
    '''List groups associated with a page.
    :param id: id of the page
    :type id: string
    :rtype: list of dictionaries
    '''

    # logic.check_access('ckanext_page_group_list', context, data_dict)

    # get a list of group ids associated with the page id
    group_id_list = PageGroupAssociation.get_group_ids_for_page(data_dict['id'])

    # group_list = []
    # if group_id_list is not None:
    #     for grp_id in group_id_list:
    #         group = logic.get_action('group_show')(context,
    #                                                {'id': grp_id, 'include_datasets': False, 'include_extras': False,
    #                                                 'include_users ': False, 'include_groups': False,
    #                                                 'include_tags': False, 'include_followers ': False})
    #         group_list.append(group)

    return group_id_list


@logic.side_effect_free
def page_list(context, data_dict):
    '''List pages user is authorized to view.
    :param limit: limits the number of pages to return (optional)
    :type limit: int
    :param offset: offsets the start of the returned list of powerviews
        (optional)
    :type offset: int
    :param id: restrict results to user with this id (optional)
    :type id: string
    :rtype: list of dictionaries
    '''

    # logic.check_access('ckanext_page_list', context, data_dict)

    query = meta.Session.query(pages_model.Page)

    limit = data_dict.get('limit')
    if limit:
        query = query.limit(limit)

    offset = data_dict.get('offset')
    if offset:
        query = query.offset(offset)

    query = query.filter_by(state='active')
    pages = query.all()

    page_dicts = []
    for p in pages:
        if data_dict.get('id_list'):
            if p.id not in data_dict.get('id_list'):
                continue
        try:
            logic.check_access('page_show', context, {'id': p.id, 'state': p.state})
        except logic.NotAuthorized:
            pass
        page_dicts.append(p.as_dict())
    return page_dicts


@logic.side_effect_free
def admin_page_list(context, data_dict):
    '''List all pages.
    :rtype: list of dictionaries
    '''

    logic.check_access('admin_page_list', context, data_dict)

    query = meta.Session.query(pages_model.Page)

    pages = query.all()

    page_dicts = []
    for p in pages:
        try:
            logic.check_access('page_show', context, {'id': p.id, 'state': p.state})
        except logic.NotAuthorized:
            pass
        else:
            page_dicts.append(p.as_dict())
    return page_dicts


@logic.side_effect_free
def group_page_list(context, data_dict):
    '''List pages associated with a group.
    :param id: id of the group
    :type id: string
    :rtype: list of dictionaries
    '''

    result = []

    pages = page_list(context, data_dict)

    for page in pages:
        pg_list = page_group_list(context, {'id': page.get('id')})
        if data_dict.get('id') in pg_list:
            result.append(page)

    return result


@logic.side_effect_free
def page_list_by_tag_id(context, data_dict):
    '''List pages associated with a tag.
    :param id: id of the tag
    :type id: string
    :rtype: list of dictionaries
    '''

    result = []
    if 'id' in data_dict:
        page_id_list = PageTagAssociation.get_page_ids_for_tag(data_dict.get('id'))
        if page_id_list:
            result = page_list(context, {'id_list': page_id_list})

    return result
