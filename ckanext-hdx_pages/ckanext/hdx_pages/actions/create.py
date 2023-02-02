import ckan.logic as logic
from ckan.plugins import toolkit
import ckanext.hdx_pages.model as pages_model
import ckanext.hdx_pages.helpers.dictize as dictize
import ckanext.hdx_pages.actions.validation as validation
import ckanext.hdx_package.helpers.helpers as pkg_h

NotFound = logic.NotFound


def page_create(context, data_dict):
    logic.check_access('page_create', context, data_dict)

    validation.page_title_validator(data_dict, context)
    validation.page_name_validator(data_dict, context)

    page = pages_model.Page(name=data_dict['name'],
                            title=data_dict.get('title'),
                            description=data_dict.get('description'),
                            type=data_dict.get('type'),
                            state=data_dict.get('state'),
                            sections=data_dict.get('sections'),
                            status=data_dict.get('status'))
    model = context['model']
    model.Session.add(page)

    for grp_id in data_dict.get('groups', []):

        # Dealing with the case where grp_id is actually the name of the group
        group_dict = logic.get_action('group_show')(context, {'id': grp_id})

        # We validate for id duplication, so this shouldn't be true during create.
        if pages_model.PageGroupAssociation.exists(page_id=page.id, group_id=group_dict.get('id')):
            raise toolkit.ValidationError("Group already associated with page.",
                                          error_summary=u"The group, {0}, is already in the page".format(
                                              group_dict.get('id')))
        # create the association
        pages_model.PageGroupAssociation.create(page=page, group_id=group_dict.get('id'), defer_commit=True)

    tags = data_dict.get('tags', [])
    tags_vocabulary = pkg_h.get_tag_vocabulary(tags)
    for tag in tags_vocabulary:
        tag_id = tag.get('id')

        if tag_id:
            # We validate for id duplication, so this shouldn't be true during create.
            if pages_model.PageTagAssociation.exists(page_id=page.id, tag_id=tag_id):
                raise toolkit.ValidationError("Tag already associated with page.",
                                              error_summary=u"The tag, {0}, is already in the page".format(
                                                  tag_id))
            # create the association
            pages_model.PageTagAssociation.create(page=page, tag_id=tag_id, defer_commit=True)
        else:
            raise logic.ValidationError({'tag_string': ["Tag %s not found" % tag.get('name')]})

    model.Session.commit()
    page_dict = dictize.page_dictize(page)
    return page_dict
