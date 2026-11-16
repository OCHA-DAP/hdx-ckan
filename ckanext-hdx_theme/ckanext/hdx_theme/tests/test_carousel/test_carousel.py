import base64
import io
import os
import uuid

import pytest

import ckan.lib.uploader as uploader
import ckan.model as model
import ckan.tests.factories as factories
import ckan.plugins.toolkit as tk
from ckan.types import Context

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==')


def _global_file_path(graphic):
    return os.path.join(uploader.get_storage_path(), 'global', os.path.basename(graphic))


@pytest.mark.usefixtures('hdx_clean_db', 'clean_index', 'with_request_context')
def test_carousel_endpoints_require_auth_token(app):
    token = factories.APIToken(expires_in=2, unit=60 * 60)['token']

    res_show_guest = app.get('/ckan-admin/carousel/show', expect_errors=True)
    assert res_show_guest.status_code == 403

    res_update_guest = app.post('/ckan-admin/carousel/update', params={
        'title': 'X',
        'url': '/x',
        'order': '1',
    }, expect_errors=True)
    assert res_update_guest.status_code == 403

    res_delete_guest = app.post('/ckan-admin/carousel/delete/some-id', expect_errors=True)
    assert res_delete_guest.status_code == 403

    user_headers = {'Authorization': token}

    res_show_user = app.get('/ckan-admin/carousel/show', headers=user_headers, expect_errors=True)
    assert res_show_user.status_code == 403

    res_update_user = app.post('/ckan-admin/carousel/update', params={
        'title': 'Y',
        'url': '/y',
        'order': '2',
    }, headers=user_headers, expect_errors=True)
    assert res_update_user.status_code == 403

    res_delete_user = app.post('/ckan-admin/carousel/delete/some-id', headers=user_headers, expect_errors=True)
    assert res_delete_user.status_code == 403


@pytest.mark.usefixtures('hdx_clean_db')
def test_carousel_update_with_file_stores_and_replaces_it(app):
    sysadmin = factories.Sysadmin()
    api_token = factories.APIToken(user=sysadmin['id'], expires_in=2, unit=60 * 60)
    admin_headers = {'Authorization': api_token['token']}

    get_action = tk.get_action
    context: Context = {'model': model, 'session': model.Session, 'user': sysadmin['name']}

    create_resp = app.post('/ckan-admin/carousel/update', params={
        'title': 'HDX HAPI',
        'url': '/hapi',
        'order': '1',
        'newTab': 'true',
        'buttonText': 'Explore',
        'graphic_upload': (io.BytesIO(PNG + b'first'), 'first.png'),
    }, headers=admin_headers)
    assert create_resp.status_code == 200

    shown = get_action('hdx_carousel_settings_show')(context, {})
    assert len(shown) == 1
    created = shown[0]
    assert created['title'] == 'HDX HAPI'
    assert created['url'] == '/hapi'
    assert created['newTab'] is True
    assert created['embed'] is False
    assert created['buttonText'] == 'Explore'
    assert created.get('id')
    first_graphic = created['graphic']
    assert first_graphic.startswith('/global/')
    assert os.path.exists(_global_file_path(first_graphic))

    update_resp = app.post('/ckan-admin/carousel/update', params={
        'id': created['id'],
        'title': 'HDX HAPI',
        'url': '/hapi',
        'order': '1',
        'newTab': 'true',
        'graphic': first_graphic,
        'graphic_upload': (io.BytesIO(PNG + b'second'), 'second.png'),
    }, headers=admin_headers)
    assert update_resp.status_code == 200

    shown = get_action('hdx_carousel_settings_show')(context, {})
    assert len(shown) == 1
    second_graphic = shown[0]['graphic']
    assert second_graphic.startswith('/global/')
    assert second_graphic != first_graphic
    assert not os.path.exists(_global_file_path(first_graphic))
    with open(_global_file_path(second_graphic), 'rb') as f:
        assert f.read() == PNG + b'second'

    os.remove(_global_file_path(second_graphic))


@pytest.mark.usefixtures('hdx_clean_db')
def test_carousel_update_with_oversized_file_is_rejected(app):
    sysadmin = factories.Sysadmin()
    api_token = factories.APIToken(user=sysadmin['id'], expires_in=2, unit=60 * 60)
    admin_headers = {'Authorization': api_token['token']}

    get_action = tk.get_action
    context: Context = {'model': model, 'session': model.Session, 'user': sysadmin['name']}

    create_resp = app.post('/ckan-admin/carousel/update', params={
        'title': 'HDX HAPI',
        'url': '/hapi',
        'order': '1',
        'newTab': 'false',
        'graphic_upload': (io.BytesIO(PNG + b'first'), 'first.png'),
    }, headers=admin_headers)
    assert create_resp.status_code == 200

    existing = get_action('hdx_carousel_settings_show')(context, {})
    graphic = existing[0]['graphic']
    files_before = sorted(os.listdir(os.path.dirname(_global_file_path(graphic))))

    max_size = tk.asint(tk.config.get('ckan.max_image_size', 2))
    update_resp = app.post('/ckan-admin/carousel/update', params={
        'id': existing[0]['id'],
        'title': 'Too large',
        'url': '/hapi',
        'order': '1',
        'newTab': 'false',
        'graphic': graphic,
        'graphic_upload': (io.BytesIO(PNG + b'0' * (max_size * 2 ** 20 + 1)), 'large.png'),
    }, headers=admin_headers, expect_errors=True)
    assert update_resp.status_code == 400
    assert 'File upload too large' in update_resp.text

    assert get_action('hdx_carousel_settings_show')(context, {}) == existing
    assert sorted(os.listdir(os.path.dirname(_global_file_path(graphic)))) == files_before

    os.remove(_global_file_path(graphic))


@pytest.mark.usefixtures('hdx_clean_db')
def test_carousel_update_with_non_image_file_is_rejected(app):
    sysadmin = factories.Sysadmin()
    api_token = factories.APIToken(user=sysadmin['id'], expires_in=2, unit=60 * 60)
    admin_headers = {'Authorization': api_token['token']}

    get_action = tk.get_action
    context: Context = {'model': model, 'session': model.Session, 'user': sysadmin['name']}

    create_resp = app.post('/ckan-admin/carousel/update', params={
        'title': 'HDX HAPI',
        'url': '/hapi',
        'order': '1',
        'newTab': 'false',
        'graphic_upload': (io.BytesIO(PNG), 'first.png'),
    }, headers=admin_headers)
    assert create_resp.status_code == 200

    existing = get_action('hdx_carousel_settings_show')(context, {})
    graphic = existing[0]['graphic']
    files_before = sorted(os.listdir(os.path.dirname(_global_file_path(graphic))))

    for content, filename in [(PNG, 'image.txt'), (b'notes', 'notes.png')]:
        update_resp = app.post('/ckan-admin/carousel/update', params={
            'id': existing[0]['id'],
            'title': 'Not an image',
            'url': '/hapi',
            'order': '1',
            'newTab': 'false',
            'graphic': graphic,
            'graphic_upload': (io.BytesIO(content), filename),
        }, headers=admin_headers, expect_errors=True)
        assert update_resp.status_code == 400
        assert 'Unsupported upload type' in update_resp.text

        assert get_action('hdx_carousel_settings_show')(context, {}) == existing
        assert sorted(os.listdir(os.path.dirname(_global_file_path(graphic)))) == files_before

    os.remove(_global_file_path(graphic))


@pytest.mark.usefixtures('hdx_clean_db')
def test_global_file_download_serves_non_images_as_attachment(app):
    name = str(uuid.uuid4())
    image_path = _global_file_path(name + '.png')
    text_path = _global_file_path(name + '.txt')
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    with open(image_path, 'wb') as f:
        f.write(PNG)
    with open(text_path, 'wb') as f:
        f.write(b'notes')

    res_image = app.get(f'/global/{name}.png')
    assert res_image.status_code == 200
    assert res_image.headers['Content-Disposition'].startswith('inline')

    res_text = app.get(f'/global/{name}.txt')
    assert res_text.status_code == 200
    assert res_text.headers['Content-Disposition'].startswith('attachment')

    os.remove(image_path)
    os.remove(text_path)


@pytest.mark.usefixtures('hdx_clean_db')
def test_carousel_delete_removes_the_file(app):
    sysadmin = factories.Sysadmin()
    api_token = factories.APIToken(user=sysadmin['id'], expires_in=2, unit=60 * 60)
    admin_headers = {'Authorization': api_token['token']}

    get_action = tk.get_action
    context: Context = {'model': model, 'session': model.Session, 'user': sysadmin['name']}

    create_resp = app.post('/ckan-admin/carousel/update', params={
        'title': 'HDX HAPI',
        'url': '/hapi',
        'order': '1',
        'newTab': 'false',
        'graphic_upload': (io.BytesIO(PNG + b'first'), 'first.png'),
    }, headers=admin_headers)
    assert create_resp.status_code == 200

    created = get_action('hdx_carousel_settings_show')(context, {})[0]
    assert os.path.exists(_global_file_path(created['graphic']))

    del_resp = app.post(f"/ckan-admin/carousel/delete/{created['id']}", headers=admin_headers)
    assert del_resp.status_code == 200
    assert del_resp.text == '[]'

    assert not os.path.exists(_global_file_path(created['graphic']))


@pytest.mark.usefixtures('hdx_clean_db')
def test_carousel_update_with_unknown_id_appends(app):
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
        'embed': False,
    }
    get_action('hdx_carousel_settings_update')(context, {'hdx.carousel.config': [existing_item]})

    update_resp = app.post('/ckan-admin/carousel/update', params={
        'id': 'unknown-id',
        'title': 'Unknown',
        'url': '/unknown',
        'order': '2',
        'newTab': 'true',
    }, headers=admin_headers)
    assert update_resp.status_code == 200

    shown = get_action('hdx_carousel_settings_show')(context, {})
    assert len(shown) == 2
    assert shown[0] == existing_item
    assert shown[1]['id'] == 'unknown-id'
    assert shown[1]['title'] == 'Unknown'
    assert shown[1]['newTab'] is True


@pytest.mark.usefixtures('hdx_clean_db')
def test_carousel_update_without_title_is_rejected(app):
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
        'embed': False,
    }
    get_action('hdx_carousel_settings_update')(context, {'hdx.carousel.config': [existing_item]})

    update_resp = app.post('/ckan-admin/carousel/update', params={
        'id': 'existing-id',
        'url': '/untitled',
        'order': '1',
        'newTab': 'false',
    }, headers=admin_headers, expect_errors=True)
    assert update_resp.status_code == 400
    assert 'Badly formatted data' in update_resp.text

    shown = get_action('hdx_carousel_settings_show')(context, {})
    assert shown == [existing_item]


@pytest.mark.usefixtures('hdx_clean_db')
def test_carousel_update_without_url_is_rejected(app):
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
        'embed': False,
    }
    get_action('hdx_carousel_settings_update')(context, {'hdx.carousel.config': [existing_item]})

    update_resp = app.post('/ckan-admin/carousel/update', params={
        'id': 'existing-id',
        'title': 'No URL',
        'order': '1',
        'newTab': 'false',
    }, headers=admin_headers, expect_errors=True)
    assert update_resp.status_code == 400
    assert 'Badly formatted data' in update_resp.text

    shown = get_action('hdx_carousel_settings_show')(context, {})
    assert shown == [existing_item]


@pytest.mark.usefixtures('hdx_clean_db')
def test_carousel_update_with_non_integer_order_is_rejected(app):
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
        'embed': False,
    }
    get_action('hdx_carousel_settings_update')(context, {'hdx.carousel.config': [existing_item]})

    update_resp = app.post('/ckan-admin/carousel/update', params={
        'id': 'existing-id',
        'title': 'Existing',
        'url': '/existing',
        'order': 'first',
        'newTab': 'false',
    }, headers=admin_headers, expect_errors=True)
    assert update_resp.status_code == 400
    assert 'Badly formatted data' in update_resp.text

    shown = get_action('hdx_carousel_settings_show')(context, {})
    assert shown == [existing_item]
