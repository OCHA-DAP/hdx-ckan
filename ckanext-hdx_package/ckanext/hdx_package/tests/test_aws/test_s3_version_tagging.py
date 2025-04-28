from typing import Dict

import pytest
import os
import boto3

from werkzeug.datastructures import FileStorage

from ckan.tests.helpers import CKANTestApp
from ckan.types import DataDict

from ckanext.hdx_theme.tests.conftest import DATASET_NAME, UserToken
from ckanext.hdx_package.tests.conftest import S3_BUCKET_NAME
from ckanext.hdx_package.tests.test_aws.constants import FILE1_NAME
from ckanext.hdx_package.helpers.constants import S3_TAG_KEY_SENSITIVE, S3_TAG_VALUE_SENSITIVE_TRUE, \
    S3_TAG_VALUE_SENSITIVE_FALSE

ServiceResource = boto3.resources.base.ServiceResource

@pytest.mark.usefixtures('hdx_s3_conn', 'keep_db_tables_on_clean', 'hdx_clean_db',
                         'dataset_with_uploaded_resource')
def test_s3_version_tagging(hdx_s3_conn: ServiceResource, sysadmin_user_with_token: UserToken,
                            app: CKANTestApp):
    file_path = os.path.join(os.path.dirname(__file__), FILE1_NAME)
    resource_name = 'test_resource_from_browser.csv'
    with open(file_path, 'rb') as f:
        file_upload = FileStorage(f)
        result_create = app.post('/api/action/resource_create',
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
        resource_dict = result_create.json['result']

    result_quarantine_tagged = _set_quarantine_flag_on_resource(
        sysadmin_user_with_token, app, resource_dict, 'true'
    )
    assert result_quarantine_tagged.status_code == 200

    try:
        tag1 = _get_resource_tag(hdx_s3_conn, resource_dict)
        assert tag1['Key'] == S3_TAG_KEY_SENSITIVE
        assert tag1['Value'] == S3_TAG_VALUE_SENSITIVE_TRUE
    except Exception as e:
        assert False

    result_quarantine_untagged = _set_quarantine_flag_on_resource(
        sysadmin_user_with_token, app, resource_dict, 'false'
    )
    assert result_quarantine_untagged.status_code == 200

    try:
        tag2 = _get_resource_tag(hdx_s3_conn, resource_dict)
        assert tag2['Key'] == S3_TAG_KEY_SENSITIVE
        assert tag2['Value'] == S3_TAG_VALUE_SENSITIVE_FALSE
    except Exception as e:
        assert False


def _set_quarantine_flag_on_resource(sysadmin_user_with_token: UserToken, app: CKANTestApp, resource_dict: DataDict,
                                     flag_value: str):
    result_quarantine = app.post('/api/action/hdx_qa_resource_patch',
                                      headers={
                                          'Authorization': str(sysadmin_user_with_token.token),

                                      },
                                      data={
                                          'id': resource_dict['id'],
                                          'in_quarantine': flag_value,
                                      })
    return result_quarantine


def _get_resource_tag(conn: ServiceResource, resource_dict: DataDict):
    key = 'resources/{}/{}'.format(resource_dict['id'], FILE1_NAME)
    tagging = conn.meta.client.get_object_tagging(Bucket=S3_BUCKET_NAME, Key=key)
    return tagging['TagSet'][0]
