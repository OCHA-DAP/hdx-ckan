import ckan.logic as logic
from ckan.plugins import toolkit
import ckanext.hdx_pages.model as pages_model
import ckanext.hdx_pages.helpers.dictize as dictize
import ckanext.hdx_pages.actions.validation as validation

from ckan.common import _


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
        model.Session.commit()

        for grp_id in data_dict.get('groups', []):
            # We validate for id duplication, so this shouldn't be true during create.
            if pages_model.PageGroupAssociation.exists(page_id=page.id, group_id=grp_id):
                raise toolkit.ValidationError("Group already associated with page.",
                                              error_summary=u"The group, {0}, is already in the page".format(
                                                  grp_id))

            # create the association
            pages_model.PageGroupAssociation.create(page_id=page.id, group_id=grp_id)

        page_dict = dictize.page_dictize(page)
        return page_dict

    except Exception as e:
        ex_msg = e.message if hasattr(e, 'message') else str(e)
        message = 'Something went wrong while processing the request: {}'.format(ex_msg)
        raise logic.ValidationError({'message': message}, error_summary=message)
