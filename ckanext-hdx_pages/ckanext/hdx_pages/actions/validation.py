import ckan.logic as logic
from ckan.common import _


def page_name_validator(page_dict, context):

    page_name = page_dict.get('name', '')

    if not page_name or not page_name.strip():
        message = _('Page name cannot be empty')
        raise logic.ValidationError({'name': [message]})

    try:
        existing_page = logic.get_action('page_show')(context, {'id': page_dict['name']})
        if existing_page and existing_page['id'] != page_dict.get('id', ''):
            message = _('Page name already exists')
            ex = logic.ValidationError({'name': [message]})
            raise ex
    except logic.NotFound, e:
        # This is good: means there's no page with the same name.
        pass
