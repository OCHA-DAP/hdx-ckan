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

    delete_result = get_action('hdx_package_links_settings_update')(
        context,
        {'hdx.package_links.config': []},
    )
    assert isinstance(delete_result, str)
    assert delete_result == '[]'

    shown_after_delete = get_action('hdx_package_links_settings_show')(context, {})
    assert shown_after_delete == []


@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
def test_package_links_guest_user_cannot_update():
    get_action = tk.get_action
    guest_context: Context = {'model': model, 'session': model.Session}

    shown = get_action('hdx_package_links_settings_show')(guest_context, {})
    assert isinstance(shown, list)

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

    shown = get_action('hdx_package_links_settings_show')(user_context, {})
    assert isinstance(shown, list)

    with pytest.raises(tk.NotAuthorized):
        get_action('hdx_package_links_settings_update')(
            user_context,
            {'hdx.package_links.config': []},
        )


@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
def test_package_links_endpoints_require_auth_token(app):
    token = factories.APIToken(expires_in=2, unit=60 * 60)['token']

    res_show_guest = app.get('/ckan-admin/package-links/show', expect_errors=True)
    assert res_show_guest.status_code == 403

    res_update_guest = app.post('/ckan-admin/package-links/update', params={
        'title': 'X',
        'url': '/dataset/x',
        'order': '1',
        'label': 'Label',
        'package_list': 'pkg-a',
    }, expect_errors=True)
    assert res_update_guest.status_code == 403

    res_delete_guest = app.post('/ckan-admin/package-links/delete/some-id', expect_errors=True)
    assert res_delete_guest.status_code == 403

    user_headers = {'Authorization': token}

    res_show_user = app.get('/ckan-admin/package-links/show', headers=user_headers, expect_errors=True)
    assert res_show_user.status_code == 403

    res_update_user = app.post('/ckan-admin/package-links/update', params={
        'title': 'Y',
        'url': '/dataset/y',
        'order': '2',
        'label': 'Label',
        'package_list': 'pkg-b',
    }, headers=user_headers, expect_errors=True)
    assert res_update_user.status_code == 403

    res_delete_user = app.post('/ckan-admin/package-links/delete/some-id', headers=user_headers, expect_errors=True)
    assert res_delete_user.status_code == 403


@pytest.mark.usefixtures('hdx_clean_db')
def test_package_links_update_and_delete_via_http_with_token(app):
    sysadmin = factories.Sysadmin()
    api_token = factories.APIToken(user=sysadmin['id'], expires_in=2, unit=60 * 60)
    admin_headers = {'Authorization': api_token['token']}

    get_action = tk.get_action
    context: Context = {'model': model, 'session': model.Session, 'user': sysadmin['name']}

    assert get_action('hdx_package_links_settings_show')(context, {}) == []

    create_resp = app.post('/ckan-admin/package-links/update', params={
        'title': 'My Package Link',
        'url': '/dataset/my-dataset',
        'order': '2',
        'newTab': 'false',
        'label': 'Datasets',
        'package_list': 'pkg-1, pkg-2',
        'buttonText': 'Open',
    }, headers=admin_headers)
    assert create_resp.status_code == 200
    assert 'My Package Link' in create_resp.text

    shown = get_action('hdx_package_links_settings_show')(context, {})
    assert isinstance(shown, list) and len(shown) == 1
    created = shown[0]
    assert created['title'] == 'My Package Link'
    assert created['url'] == '/dataset/my-dataset'
    assert created['order'] == 2
    assert created['newTab'] is False
    assert created['label'] == 'Datasets'
    assert created['package_list'] == 'pkg-1,pkg-2'
    assert created.get('buttonText') == 'Open'
    assert created.get('id')

    del_resp = app.post(f"/ckan-admin/package-links/delete/{created['id']}", headers=admin_headers)
    assert del_resp.status_code == 200

    shown_after_delete = get_action('hdx_package_links_settings_show')(context, {})
    assert shown_after_delete == []
