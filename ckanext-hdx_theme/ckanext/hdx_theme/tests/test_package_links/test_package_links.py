import pytest

import ckan.model as model
import ckan.tests.factories as factories
import ckan.plugins.toolkit as tk
from ckan.types import Context


@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
def test_package_links_actions_end_to_end():
    sysadmin = factories.Sysadmin()
    context: Context = {'model': model, 'session': model.Session, 'user': sysadmin['name']}
    get_action = tk.get_action

    # Show should be empty at start
    shown = get_action('hdx_package_links_settings_show')(context, {})
    assert isinstance(shown, list)
    assert shown == []

    create_item = {
        'title': 'My Package Link',
        'url': '/dataset/my-dataset',
        'order': 2,
        'newTab': False,
        'label': 'Datasets',
        'package_list': 'pkg-1,pkg-2',
        'buttonText': 'Open',
    }
    result = get_action('hdx_package_links_settings_update')(
        context,
        {'hdx.package_links.config': [create_item]},
    )
    assert isinstance(result, str)
    assert result == '[{"title": "My Package Link", "url": "/dataset/my-dataset", "order": 2, "newTab": false, "label": "Datasets", "package_list": "pkg-1,pkg-2", "buttonText": "Open"}]'

    # Show should return the newly created item
    shown_after_create = get_action('hdx_package_links_settings_show')(context, {})
    assert len(shown_after_create) == 1
    created = shown_after_create[0]
    assert created['title'] == 'My Package Link'
    assert created['url'] == '/dataset/my-dataset'
    assert created['order'] == 2
    assert created['newTab'] is False
    assert created['label'] == 'Datasets'
    assert created['package_list'] == 'pkg-1,pkg-2'
    assert created['buttonText'] == 'Open'

    # Delete the item by updating the config to an empty list
    delete_result = get_action('hdx_package_links_settings_update')(
        context,
        {'hdx.package_links.config': []},
    )
    assert isinstance(delete_result, str)
    assert delete_result == '[]'

    # Show should be empty again
    shown_after_delete = get_action('hdx_package_links_settings_show')(context, {})
    assert shown_after_delete == []


@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
def test_package_links_guest_user_cannot_update():
    get_action = tk.get_action
    guest_context: Context = {'model': model, 'session': model.Session}

    # Guest can view
    shown = get_action('hdx_package_links_settings_show')(guest_context, {})
    assert isinstance(shown, list)

    # Guest cannot update
    with pytest.raises(tk.NotAuthorized):
        get_action('hdx_package_links_settings_update')(
            guest_context,
            {'hdx.package_links.config': []},
        )


@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
def test_package_links_regular_user_cannot_update():
    user = factories.User()
    user_context: Context = {'model': model, 'session': model.Session, 'user': user['name']}
    get_action = tk.get_action

    # Regular user can view
    shown = get_action('hdx_package_links_settings_show')(user_context, {})
    assert isinstance(shown, list)

    # Regular user cannot update
    with pytest.raises(tk.NotAuthorized):
        get_action('hdx_package_links_settings_update')(
            user_context,
            {'hdx.package_links.config': []},
        )
