import logging
import ckan.logic as logic
import ckan.plugins.toolkit as tk
from ckan.common import _

log = logging.getLogger(__name__)
abort = tk.abort


def page_name_validator(page_dict, context):
    page_name = page_dict.get('name', '')

    if not page_name or not page_name.strip():
        message = _('Page name cannot be empty')
        raise logic.ValidationError({'name': [message]})

    try:
        existing_page = logic.get_action('page_show')(context, {'id': page_dict.get('name')})
        if existing_page and existing_page.get('id') != page_dict.get('id') and page_dict.get('id') != page_dict.get(
            'name'):
            raise logic.ValidationError({'name': [_('Page name already exists')]})
    except logic.NotFound as e:
        # This is good: means there's no page with the same name.
        pass


def page_title_validator(page_dict, context):
    page_title = page_dict.get('title', '')
    if not page_title or not page_title.strip():
        message = _('Page title cannot be empty')
        raise logic.ValidationError({'title': [message]})


def page_id_validator(page, context):
    if not page:
        abort(404, _('Page not found'))
