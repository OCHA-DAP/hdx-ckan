import json
import os

import mock
import pytest
from werkzeug.datastructures import FileStorage

import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.tests.helpers import CKANTestApp

from ckanext.hdx_package.tests.test_aws.constants import FILE1_NAME
from ckanext.hdx_theme.tests.conftest import DATASET_NAME, UserToken

_get_action = tk.get_action
url_for = tk.url_for


@pytest.mark.usefixtures('hdx_s3_conn', 'keep_db_tables_on_clean', 'hdx_clean_db',
                         'dataset_with_uploaded_resource')
@mock.patch('ckanext.hdx_package.views.download_wrapper.view')
def test_metadata_saved_on_create(mock_view: mock.MagicMock, sysadmin_user_with_token: UserToken, app: CKANTestApp):
    mock_view.return_value = json.dumps({'success': True})
    mock_view.download.return_value = json.dumps({'success': True})
    file_path = os.path.join(os.path.dirname(__file__), FILE1_NAME)
    resource_name = 'test_resource_from_browser.csv'
    with open(file_path, 'rb') as f:
        file_upload = FileStorage(f)
        result = app.post('/api/action/resource_create',
                               headers={
                                   'Authorization': str(sysadmin_user_with_token.token),

                               },
                               data={
                                   'package_id': DATASET_NAME,
                                   'name': resource_name,
                                   'url_type': 'upload',
                                   'resource_type': 'file.upload',
                                   'upload': file_upload
                               })
    resource_dict = result.json['result']
    assert resource_dict.get('download_url').split('/download/')[0] + '/download/' == resource_dict.get('alt_url')

    result = app.post('/api/action/resource_create',
                           headers={
                               'Authorization': str(sysadmin_user_with_token.token),

                           },
                           data={
                               'package_id': DATASET_NAME,
                               'name': 'test external url',
                               'url': 'https://centre.humdata.org',
                               'url_type': 'api',
                               'resource_type': 'api',
                               'format': 'API'
                           })
    context = {'model': model, 'session': model.Session, 'user': sysadmin_user_with_token.username}
    pkg_dict = _get_action('package_show')(context, {'id': DATASET_NAME})

    result = app.get(url_for("hdx_download_wrapper.download_at_position", id=DATASET_NAME, n=0))
    assert '{"success": true}' in result.body

    result = app.get(url_for("hdx_download_wrapper.download_at_position", id=DATASET_NAME, n=1))
    assert '{"success": true}' in result.body

    result = app.get(url_for("hdx_download_wrapper.download_at_position", id=DATASET_NAME, n=2),
                          follow_redirects=False)
    assert 'https://centre.humdata.org' in result.body
