import pytest
import os
import boto3
from typing import Dict

from werkzeug.datastructures import FileStorage

from ckan.tests.helpers import CKANTestApp
from ckan.types import DataDict

from ckanext.hdx_theme.tests.conftest import DATASET_NAME, UserToken
from ckanext.hdx_package.tests.test_aws.constants import FILE1_NAME
from ckanext.hdx_package.tests.test_aws.util import fetch_s3_object


ServiceResource = boto3.resources.base.ServiceResource


TEST_DATA = [
    {
        'user_agent': '',
        'autoscan': False,
    },
    {
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36',
        'autoscan': True,
    },
    {
        'user_agent': 'HDXINTERNAL:HDXPythonLibrary/4.9.9-FTS',
        'autoscan': False,
    },

]


@pytest.mark.usefixtures('hdx_s3_conn', 'keep_db_tables_on_clean', 'hdx_clean_db',
                         'dataset_with_uploaded_resource')
@pytest.mark.parametrize('test_item', TEST_DATA)
def test_metadata_saved_on_create(hdx_s3_conn: ServiceResource, sysadmin_user_with_token: UserToken, app: CKANTestApp,
                                  test_item: Dict[str, any]):
    file_path = os.path.join(os.path.dirname(__file__), FILE1_NAME)
    resource_name = 'test_resource_from_browser.csv'
    with open(file_path, 'rb') as f:
        file_upload = FileStorage(f)
        result = app.post('/api/action/resource_create',
                               headers={
                                   'Authorization': str(sysadmin_user_with_token.token),
                                   'User-Agent': test_item['user_agent']
                               },
                               data={
                                   'package_id': DATASET_NAME,
                                   'name': resource_name,
                                   'url_type': 'upload',
                                   'resource_type': 'file.upload',
                                   'upload': file_upload
                               })
    resource_dict = result.json['result']
    s3obj = fetch_s3_object(hdx_s3_conn, resource_dict['id'], FILE1_NAME)
    assert test_item['autoscan'] == bool(s3obj.get('Metadata', {}).get('autoscan'))

    assert resource_dict.get('download_url').split('/download/')[0]+'/download/' == resource_dict.get('alt_url')


@pytest.mark.usefixtures('hdx_s3_conn', 'keep_db_tables_on_clean', 'hdx_clean_db',
                         'dataset_with_uploaded_resource')
@pytest.mark.parametrize('test_item', TEST_DATA)
def test_metadata_saved_on_update(hdx_s3_conn: ServiceResource, sysadmin_user_with_token: UserToken,
                                  dataset_with_uploaded_resource: DataDict, app: CKANTestApp,
                                  test_item: Dict[str, any]):
    file_path = os.path.join(os.path.dirname(__file__), FILE1_NAME)
    with open(file_path, 'rb') as f:
        file_upload = FileStorage(f)
        result = app.post('/api/action/resource_update',
                               headers={
                                   'Authorization': str(sysadmin_user_with_token.token),
                                   'User-Agent': test_item['user_agent']
                               },
                               data={
                                   'id': dataset_with_uploaded_resource['resources'][0]['id'],
                                   'url_type': 'upload',
                                   'resource_type': 'file.upload',
                                   'upload': file_upload,
                                   'name': 'test_resource_from_browser.csv',
                               })
    resource_dict = result.json['result']
    s3obj = fetch_s3_object(hdx_s3_conn, resource_dict['id'], FILE1_NAME)
    assert test_item['autoscan'] == bool(s3obj.get('Metadata', {}).get('autoscan'))

    assert resource_dict.get('download_url').split('/download/')[0] + '/download/' == resource_dict.get('alt_url')


@pytest.mark.usefixtures('hdx_s3_conn', 'keep_db_tables_on_clean', 'hdx_clean_db',
                         'dataset_with_uploaded_resource')
@pytest.mark.parametrize('test_item', TEST_DATA)
def test_metadata_saved_on_revise(hdx_s3_conn: ServiceResource, sysadmin_user_with_token: UserToken,
                                  dataset_with_uploaded_resource: DataDict, app: CKANTestApp,
                                  test_item: Dict[str, any]):
    file_path = os.path.join(os.path.dirname(__file__), FILE1_NAME)
    with open(file_path, 'rb') as f:
        file_upload = FileStorage(f)
        result = app.post('/api/action/package_revise',
                               headers={
                                   'Authorization': str(sysadmin_user_with_token.token),
                                   'User-Agent': test_item['user_agent']
                               },
                               data={
                                   'match__name': DATASET_NAME,
                                   'update__resources__0__url_type': 'upload',
                                   'update__resources__0__resource_type': 'file.upload',
                                   'update__resources__0__upload': file_upload,
                                   'update__resources__0__name': 'test_resource_from_browser.csv',
                               })
    s3obj = fetch_s3_object(hdx_s3_conn, dataset_with_uploaded_resource['resources'][0]['id'], FILE1_NAME)
    assert test_item['autoscan'] == bool(s3obj.get('Metadata', {}).get('autoscan'))
