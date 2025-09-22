import pytest

import ckan.model as model
import ckan.tests.factories as factories
import ckan.plugins.toolkit as tk
from ckan.types import Context


@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
def test_quick_links_actions_end_to_end():
    sysadmin = factories.Sysadmin()
    context: Context = {'model': model, 'session': model.Session, 'user': sysadmin['name']}

    get_action = tk.get_action

    # Show should be empty at start
    shown = get_action('hdx_quick_links_settings_show')(context, {})
    assert isinstance(shown, list)
    assert shown == []

    create_item = {
        'title': 'My Link',
        'url': '/my-link',
        'order': 1,
        'newTab': True,
        'archived': False,
        'buttonText': 'Go',
    }
    result = get_action('hdx_quick_links_settings_update')(
        context,
        {'hdx.quick_links.config': [create_item]},
    )
    assert isinstance(result, str)
    assert result == '[{"title": "My Link", "url": "/my-link", "order": 1, "newTab": true, "archived": false, "buttonText": "Go"}]'

    # Show should return the newly created item with a generated id
    shown_after_create = get_action('hdx_quick_links_settings_show')(context, {})
    assert len(shown_after_create) == 1
    created = shown_after_create[0]
    assert created['title'] == 'My Link'
    assert created['url'] == '/my-link'
    assert created['newTab'] is True
    assert created['archived'] is False
    assert created['buttonText'] == 'Go'

    # Delete the item by updating the config to an empty list
    delete_result = get_action('hdx_quick_links_settings_update')(
        context,
        {'hdx.quick_links.config': []},
    )
    assert isinstance(delete_result, str)
    assert delete_result == '[]'

    # Show should be empty again
    shown_after_delete = get_action('hdx_quick_links_settings_show')(context, {})
    assert shown_after_delete == []


@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
def test_quick_links_guest_user_cannot_update():
    get_action = tk.get_action
    guest_context: Context = {'model': model, 'session': model.Session}

    # Guest can view
    shown = get_action('hdx_quick_links_settings_show')(guest_context, {})
    assert isinstance(shown, list)

    # Guest cannot update
    with pytest.raises(tk.NotAuthorized):
        get_action('hdx_quick_links_settings_update')(
            guest_context,
            {'hdx.quick_links.config': []},
        )


@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
def test_quick_links_regular_user_cannot_update():
    user = factories.User()
    user_context: Context = {'model': model, 'session': model.Session, 'user': user['name']}
    get_action = tk.get_action

    # Regular user can view
    shown = get_action('hdx_quick_links_settings_show')(user_context, {})
    assert isinstance(shown, list)

    # Regular user cannot update
    with pytest.raises(tk.NotAuthorized):
        get_action('hdx_quick_links_settings_update')(
            user_context,
            {'hdx.quick_links.config': []},
        )
