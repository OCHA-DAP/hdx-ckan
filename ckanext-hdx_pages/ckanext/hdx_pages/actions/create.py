import ckan.logic as logic
from ckan.plugins import toolkit
import ckanext.hdx_pages.model as pages_model
import ckanext.hdx_pages.helpers.dictize as dictize
import ckanext.hdx_pages.actions.validation as validation


def page_create(context, data_dict):
    model = context['model']

    logic.check_access('page_create', context, data_dict)

    validation.page_name_validator(data_dict, context)

    try:
        page = pages_model.Page(name=data_dict['name'],
                                title=data_dict.get('title'),
                                description=data_dict.get('description'),
                                type=data_dict.get('type'),
                                state=data_dict.get('state'),
                                sections=data_dict.get('sections'),
                                status=data_dict.get('status'))
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

        for tag in data_dict.get('tags', []):

            if tag.get('name') and tag.get('vocabulary_id'):
                tag_dict = logic.get_action('tag_show')(context, {'id': tag.get('name'),
                                                                  'vocabulary_id':tag.get('vocabulary_id')})

                # We validate for id duplication, so this shouldn't be true during create.
                if pages_model.PageTagAssociation.exists(page_id=page.id, tag_id=tag_dict.get('id')):
                    raise toolkit.ValidationError("Tag already associated with page.",
                                                  error_summary=u"The tag, {0}, is already in the page".format(
                                                      tag_dict.get('id')))

                # create the association
                pages_model.PageTagAssociation.create(page=page, tag_id=tag_dict.get('id'), defer_commit=True)

        model.Session.commit()
        page_dict = dictize.page_dictize(page)
        return page_dict

    except Exception as e:
        ex_msg = e.message if hasattr(e, 'message') else str(e)
        message = 'Something went wrong while processing the request: {}'.format(ex_msg)
        raise logic.ValidationError({'message': message}, error_summary=message)
