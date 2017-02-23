import datetime

import ckan.logic as logic

import ckanext.hdx_pages.model as pages_model
import ckanext.hdx_pages.helpers.dictize as dictize
import ckanext.hdx_pages.actions.validation as validation

NotFound = logic.NotFound


def page_update(context, data_dict):
    logic.check_access('page_update', context, data_dict)

    validation.page_name_validator(data_dict, context)

    try:
        session = context['session']
        page = pages_model.Page.get_by_id(id=data_dict['id'])
        if page is None:
            raise NotFound

        populate_page(page, data_dict)

        groups = data_dict.get('groups')
        process_groups(page, groups)

        session.add(page)
        session.commit()
        return dictize.page_dictize(page)
    except Exception as e:
        ex_msg = e.message if hasattr(e, 'message') else str(e)
        message = 'Something went wrong while processing the request: {}'.format(ex_msg)
        raise logic.ValidationError({'message': message}, error_summary=message)


def process_groups(page, groups):
    # the original id list
    grp_ids = pages_model.PageGroupAssociation.get_group_ids_for_page(page.id)

    # remove current assigned groups
    for grp_id in grp_ids:
        assoc = pages_model.PageGroupAssociation.get(page_id=page.id, group_id=grp_id)
        assoc.delete()

    # add new ids
    for grp_id in groups:
        pages_model.PageGroupAssociation.create(page=page, group_id=grp_id, defer_commit=True)


def populate_page(page, data_dict):
    page.name = data_dict['name']
    page.title = data_dict['title']
    page.description = data_dict.get('description')
    page.type = data_dict.get('type')
    page.state = data_dict.get('state')
    page.sections = data_dict.get('sections')
    page.status = data_dict.get('status')
    page.modified = datetime.datetime.now()
