import datetime

import ckan.logic as logic

import ckanext.hdx_pages.model as pages_model
import ckanext.hdx_pages.helpers.dictize as dictize
import ckanext.hdx_pages.actions.validation as validation
import ckanext.hdx_package.helpers.helpers as pkg_h

NotFound = logic.NotFound


def page_update(context, data_dict):
    logic.check_access('page_update', context, data_dict)

    page = pages_model.Page.get_by_id(id=data_dict['id'])
    validation.page_id_validator(page, context)
    validation.page_title_validator(data_dict, context)
    validation.page_name_validator(data_dict, context)

    populate_page(page, data_dict)

    groups = data_dict.get('groups')
    process_groups(context, page, groups)

    tags = data_dict.get('tags')
    process_tags(context, page, tags)

    session = context['session']
    session.add(page)
    session.commit()
    return dictize.page_dictize(page)


def process_groups(context, page, groups):
    # the original id list
    grp_ids = pages_model.PageGroupAssociation.get_group_ids_for_page(page.id)

    # remove current assigned groups
    for grp_id in grp_ids:
        assoc = pages_model.PageGroupAssociation.get(page_id=page.id, group_id=grp_id)
        assoc.delete()

    # add new ids
    if groups:
        for grp_id in groups:
            group_dict = logic.get_action('group_show')(context, {'id': grp_id})
            pages_model.PageGroupAssociation.create(page=page, group_id=group_dict.get('id'), defer_commit=True)


def process_tags(context, page, tags):
    # the original id list
    tag_ids = pages_model.PageTagAssociation.get_tag_ids_for_page(page.id)

    # remove current assigned tags
    for tag_id in tag_ids:
        assoc = pages_model.PageTagAssociation.get(page_id=page.id, tag_id=tag_id)
        assoc.delete()

    # add new ids
    if tags:
        tags_vocabulary = pkg_h.get_tag_vocabulary(tags)
        for tag in tags_vocabulary:
            tag_id = tag.get('id')

            if tag_id:
                pages_model.PageTagAssociation.create(page=page, tag_id=tag.get('id'), defer_commit=True)
            else:
                raise logic.ValidationError({'tag_string': ["Tag %s not found" % tag.get('name')]})


def populate_page(page, data_dict):
    page.name = data_dict['name']
    page.title = data_dict['title']
    page.description = data_dict.get('description')
    page.type = data_dict.get('type')
    page.state = data_dict.get('state')
    page.sections = data_dict.get('sections')
    page.status = data_dict.get('status')
    page.modified = datetime.datetime.now()
