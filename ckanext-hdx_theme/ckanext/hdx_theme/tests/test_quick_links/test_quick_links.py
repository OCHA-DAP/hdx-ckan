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

    shown_after_create = get_action('hdx_quick_links_settings_show')(context, {})
    assert len(shown_after_create) == 1
    created = shown_after_create[0]
    assert created['title'] == 'My Link'
    assert created['url'] == '/my-link'
    assert created['newTab'] is True
    assert created['archived'] is False
    assert created['buttonText'] == 'Go'

    delete_result = get_action('hdx_quick_links_settings_update')(
        context,
        {'hdx.quick_links.config': []},
    )
    assert isinstance(delete_result, str)
    assert delete_result == '[]'

    shown_after_delete = get_action('hdx_quick_links_settings_show')(context, {})
    assert shown_after_delete == []


@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
def test_quick_links_guest_user_cannot_update():
    get_action = tk.get_action
    guest_context: Context = {'model': model, 'session': model.Session}

    shown = get_action('hdx_quick_links_settings_show')(guest_context, {})
    assert isinstance(shown, list)

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

    shown = get_action('hdx_quick_links_settings_show')(user_context, {})
    assert isinstance(shown, list)

    with pytest.raises(tk.NotAuthorized):
        get_action('hdx_quick_links_settings_update')(
            user_context,
            {'hdx.quick_links.config': []},
        )


@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
def test_quick_links_endpoints_require_auth_token(app):
    token = factories.APIToken(expires_in=2, unit=60 * 60)['token']

    res_show_guest = app.get('/ckan-admin/quick-links/show', expect_errors=True)
    assert res_show_guest.status_code == 403

    res_update_guest = app.post('/ckan-admin/quick-links/update', params={
        'title': 'X',
        'url': '/x',
        'order': '1',
    }, expect_errors=True)
    assert res_update_guest.status_code == 403

    res_delete_guest = app.post('/ckan-admin/quick-links/delete/some-id', expect_errors=True)
    assert res_delete_guest.status_code == 403

    user_headers = {'Authorization': token}

    res_show_user = app.get('/ckan-admin/quick-links/show', headers=user_headers, expect_errors=True)
    assert res_show_user.status_code == 403

    res_update_user = app.post('/ckan-admin/quick-links/update', params={
        'title': 'Y',
        'url': '/y',
        'order': '2',
    }, headers=user_headers, expect_errors=True)
    assert res_update_user.status_code == 403

    res_delete_user = app.post('/ckan-admin/quick-links/delete/some-id', headers=user_headers, expect_errors=True)
    assert res_delete_user.status_code == 403


@pytest.mark.usefixtures('hdx_clean_db')
def test_quick_links_update_and_delete_via_http_with_token(app):
    sysadmin = factories.Sysadmin()
    api_token = factories.APIToken(user=sysadmin['id'], expires_in=2, unit=60 * 60)
    admin_headers = {'Authorization': api_token['token']}

    get_action = tk.get_action
    context: Context = {'model': model, 'session': model.Session, 'user': sysadmin['name']}

    assert get_action('hdx_quick_links_settings_show')(context, {}) == []

    create_resp = app.post('/ckan-admin/quick-links/update', params={
        'title': 'My Link',
        'url': '/my-link',
        'order': '1',
        'newTab': 'true',
        'archived': 'false',
        'buttonText': 'Go',
    }, headers=admin_headers)
    assert create_resp.status_code == 200
    assert 'My Link' in create_resp.text

    shown = get_action('hdx_quick_links_settings_show')(context, {})
    assert isinstance(shown, list) and len(shown) == 1
    created = shown[0]
    assert created['title'] == 'My Link'
    assert created['url'] == '/my-link'
    assert created['order'] == 1
    assert created['newTab'] is True
    assert created['archived'] is False
    assert created.get('buttonText') == 'Go'
    assert created.get('id')

    del_resp = app.post(f"/ckan-admin/quick-links/delete/{created['id']}", headers=admin_headers)
    assert del_resp.status_code == 200

    shown_after_delete = get_action('hdx_quick_links_settings_show')(context, {})
    assert shown_after_delete == []


@pytest.mark.usefixtures('hdx_clean_db')
def test_quick_links_update_with_unknown_id_appends(app):
    sysadmin = factories.Sysadmin()
    api_token = factories.APIToken(user=sysadmin['id'], expires_in=2, unit=60 * 60)
    admin_headers = {'Authorization': api_token['token']}

    get_action = tk.get_action
    context: Context = {'model': model, 'session': model.Session, 'user': sysadmin['name']}

    existing_item = {
        'id': 'existing-id',
        'title': 'Existing',
        'url': '/existing',
        'order': 1,
        'newTab': False,
        'archived': False,
    }
    get_action('hdx_quick_links_settings_update')(context, {'hdx.quick_links.config': [existing_item]})

    update_resp = app.post('/ckan-admin/quick-links/update', params={
        'id': 'unknown-id',
        'title': 'Unknown',
        'url': '/unknown',
        'order': '2',
        'newTab': 'true',
        'archived': 'true',
    }, headers=admin_headers)
    assert update_resp.status_code == 200

    shown = get_action('hdx_quick_links_settings_show')(context, {})
    assert len(shown) == 2
    assert shown[0] == existing_item
    assert shown[1]['id'] == 'unknown-id'
    assert shown[1]['title'] == 'Unknown'
    assert shown[1]['newTab'] is True
    assert shown[1]['archived'] is True


@pytest.mark.usefixtures('hdx_clean_db')
def test_quick_links_update_without_title_is_rejected(app):
    sysadmin = factories.Sysadmin()
    api_token = factories.APIToken(user=sysadmin['id'], expires_in=2, unit=60 * 60)
    admin_headers = {'Authorization': api_token['token']}

    get_action = tk.get_action
    context: Context = {'model': model, 'session': model.Session, 'user': sysadmin['name']}

    existing_item = {
        'id': 'existing-id',
        'title': 'Existing',
        'url': '/existing',
        'order': 1,
        'newTab': False,
        'archived': False,
    }
    get_action('hdx_quick_links_settings_update')(context, {'hdx.quick_links.config': [existing_item]})

    update_resp = app.post('/ckan-admin/quick-links/update', params={
        'id': 'existing-id',
        'url': '/untitled',
        'order': '1',
        'newTab': 'false',
        'archived': 'false',
    }, headers=admin_headers, expect_errors=True)
    assert update_resp.status_code == 400
    assert 'Badly formatted data' in update_resp.text

    shown = get_action('hdx_quick_links_settings_show')(context, {})
    assert shown == [existing_item]


@pytest.mark.usefixtures('hdx_clean_db')
def test_quick_links_update_without_url_is_rejected(app):
    sysadmin = factories.Sysadmin()
    api_token = factories.APIToken(user=sysadmin['id'], expires_in=2, unit=60 * 60)
    admin_headers = {'Authorization': api_token['token']}

    get_action = tk.get_action
    context: Context = {'model': model, 'session': model.Session, 'user': sysadmin['name']}

    existing_item = {
        'id': 'existing-id',
        'title': 'Existing',
        'url': '/existing',
        'order': 1,
        'newTab': False,
        'archived': False,
    }
    get_action('hdx_quick_links_settings_update')(context, {'hdx.quick_links.config': [existing_item]})

    update_resp = app.post('/ckan-admin/quick-links/update', params={
        'id': 'existing-id',
        'title': 'No URL',
        'order': '1',
        'newTab': 'false',
        'archived': 'false',
    }, headers=admin_headers, expect_errors=True)
    assert update_resp.status_code == 400
    assert 'Badly formatted data' in update_resp.text

    shown = get_action('hdx_quick_links_settings_show')(context, {})
    assert shown == [existing_item]
