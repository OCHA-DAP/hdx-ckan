import pytest
import boto3

from copy import deepcopy
from moto import mock_aws

from ckan.types import Config

from ckanext.hdx_theme.tests.conftest import keep_db_tables_on_clean, dataset_with_uploaded_resource, \
    sysadmin_user_with_token, hdx_with_plugins, hdx_clean_db


S3_BUCKET_NAME = 'some-bucket-name'

@pytest.fixture()
def hdx_change_s3_config(ckan_config: Config) -> None:
    original_config = deepcopy(ckan_config)

    if 's3filestore' not in ckan_config['ckan.plugins']:
        ckan_config['ckan.plugins'].append('s3filestore')
    ## AWS S3 settings
    ckan_config['ckanext.s3filestore.aws_access_key_id'] = 'aws_access_key_id'
    ckan_config['ckanext.s3filestore.aws_secret_access_key'] = 'aws_secret_access_key'
    ckan_config['ckanext.s3filestore.aws_bucket_name'] = S3_BUCKET_NAME
    ckan_config['ckanext.s3filestore.host_name'] = 'http://s3.eu-central-1.amazonaws.com'
    ckan_config['ckanext.s3filestore.region_name'] = 'eu-central-1'
    ckan_config['ckanext.s3filestore.signature_version'] = 's3v4'
    ckan_config['ckanext.s3filestore.link_expires_in_seconds'] = 180

    ckan_config.pop('hdx.s3filestore', None)

    yield

    plugins = ckan_config.get('ckan.plugins', [])
    plugins.pop() if len(plugins) > 0 and plugins[-1] == 's3filestore' else None
    ckan_config.clear()
    ckan_config.update(deepcopy(original_config))

@pytest.fixture()
def hdx_s3_conn(ckan_config: Config, hdx_change_s3_config: None) -> boto3.resources.base.ServiceResource:
    m_aws = mock_aws()
    m_aws.start()

    region_name = ckan_config['ckanext.s3filestore.region_name']
    bucket_name = ckan_config['ckanext.s3filestore.aws_bucket_name']
    conn = boto3.resource('s3', region_name=region_name)
    conn.create_bucket(Bucket=bucket_name, CreateBucketConfiguration={'LocationConstraint': '{}'.format(region_name)})

    yield conn

    m_aws.stop()
