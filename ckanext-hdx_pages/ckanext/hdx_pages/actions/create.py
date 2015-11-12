import ckan.logic as logic

import ckanext.hdx_pages.model as pages_model
import ckanext.hdx_pages.helpers.dictize as dictize


def page_create(context, data_dict):
    model = context['model']

    try:
        page = pages_model.Page(name=data_dict['name'], title=data_dict.get('title'),
                                description=data_dict.get('description'),
                                type=data_dict.get('type'), sections=data_dict.get('sections'))
        model.Session.add(page)
        model.Session.commit()

        page_dict = dictize.page_dictize(page)
        return page_dict

    except Exception as e:
        ex_msg = e.message if hasattr(e, 'message') else str(e)
        message = 'Something went wrong while processing the request: {}'.format(ex_msg)
        raise logic.ValidationError({'message': message}, error_summary=message)
