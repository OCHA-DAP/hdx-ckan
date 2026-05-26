# -*- coding: utf-8 -*-
"""
Unit tests for _create_s3_client() in s3_version_tagger.py.

The end-to-end integration path (tag_s3_version via API + moto) is covered by
test_s3_version_tagging.py.  Here we test only the credential-selection logic
added by HDX-11529: _create_s3_client() must use AssumeRole credentials when
ckanext.s3filestore.aws_use_assume_role is True, and static keys otherwise.
"""
from unittest import mock

import pytest

from ckanext.hdx_package.helpers.constants import (
    S3_TAG_KEY_SENSITIVE,
    S3_TAG_VALUE_SENSITIVE_FALSE,
    S3_TAG_VALUE_SENSITIVE_TRUE,
)
from ckanext.hdx_package.helpers.s3_version_tagger import (
    S3VersionTaggingException,
    _create_s3_client,
    tag_s3_version,
)

_FAKE_ASSUMED_CREDS = {
    'access_key': 'ASSUMED_KEY',
    'secret_key': 'ASSUMED_SECRET',
    'session_token': 'ASSUMED_TOKEN',
    'expiration': None,
    'region': 'eu-central-1',
}

_BASE_CONFIG = {
    'ckanext.s3filestore.region_name': 'eu-central-1',
    'ckanext.s3filestore.signature_version': 's3v4',
    'ckanext.s3filestore.host_name': None,
    'ckanext.s3filestore.aws_bucket_name': 'hdx-test-bucket',
}


def _config_mock(**overrides):
    """Return a mock that mimics tk.config.get() with the given key→value map."""
    values = {**_BASE_CONFIG, **overrides}
    m = mock.MagicMock()
    m.get.side_effect = lambda key, default=None: values.get(key, default)
    return m


# ---------------------------------------------------------------------------
# _create_s3_client – credential-selection logic (HDX-11529)
# ---------------------------------------------------------------------------

@mock.patch('ckanext.s3filestore.caching.get_cached_s3_credentials')
@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger.boto3.Session')
@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger._config')
def test_create_s3_client_assume_role_uses_cached_credentials(
    mock_config, mock_session_cls, mock_get_creds
):
    """AssumeRole mode: session is built from get_cached_s3_credentials(), not static keys."""
    mock_config.get.side_effect = _config_mock(
        **{'ckanext.s3filestore.aws_use_assume_role': True}
    ).get.side_effect
    mock_get_creds.return_value = _FAKE_ASSUMED_CREDS

    _create_s3_client()

    mock_get_creds.assert_called_once()
    mock_session_cls.assert_called_once_with(
        aws_access_key_id='ASSUMED_KEY',
        aws_secret_access_key='ASSUMED_SECRET',
        aws_session_token='ASSUMED_TOKEN',
        region_name='eu-central-1',
    )


@mock.patch('ckanext.s3filestore.caching.get_cached_s3_credentials')
@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger.boto3.Session')
@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger._config')
def test_create_s3_client_assume_role_session_includes_token(
    mock_config, mock_session_cls, mock_get_creds
):
    """AssumeRole mode: boto3.Session must receive aws_session_token (required by STS)."""
    mock_config.get.side_effect = _config_mock(
        **{'ckanext.s3filestore.aws_use_assume_role': True}
    ).get.side_effect
    mock_get_creds.return_value = _FAKE_ASSUMED_CREDS

    _create_s3_client()

    _, kwargs = mock_session_cls.call_args
    assert 'aws_session_token' in kwargs
    assert kwargs['aws_session_token'] == 'ASSUMED_TOKEN'


@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger.boto3.session.Session')
@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger._config')
def test_create_s3_client_static_mode_uses_config_keys(mock_config, mock_session_cls):
    """Static mode: session is built with p_key/s_key from config, no session token."""
    mock_config.get.side_effect = _config_mock(**{
        'ckanext.s3filestore.aws_use_assume_role': False,
        'ckanext.s3filestore.aws_access_key_id': 'STATIC_KEY',
        'ckanext.s3filestore.aws_secret_access_key': 'STATIC_SECRET',
    }).get.side_effect

    _create_s3_client()

    mock_session_cls.assert_called_once_with(
        aws_access_key_id='STATIC_KEY',
        aws_secret_access_key='STATIC_SECRET',
        region_name='eu-central-1',
    )
    # Must not pass a session token in static mode
    _, kwargs = mock_session_cls.call_args
    assert 'aws_session_token' not in kwargs


# ---------------------------------------------------------------------------
# tag_s3_version – put_object_tagging arguments
# ---------------------------------------------------------------------------

@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger.S3ResourceUploader')
@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger._create_s3_client')
@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger._config')
def test_tag_s3_version_quarantine_true_sets_sensitive_yes(
    mock_config, mock_create_client, mock_uploader_cls
):
    """in_quarantine=True → Sensitive tag value is 'yes'."""
    mock_config.get.return_value = 'hdx-test-bucket'
    mock_client = mock.MagicMock()
    mock_create_client.return_value = mock_client
    mock_uploader_cls.return_value.get_path.return_value = 'resources/res-id/file.csv'

    tag_s3_version('res-id', 'file.csv', in_quarantine=True, dataset_name='my-dataset')

    mock_client.put_object_tagging.assert_called_once()
    tag_set = mock_client.put_object_tagging.call_args[1]['Tagging']['TagSet']
    sensitive_tag = next(t for t in tag_set if t['Key'] == S3_TAG_KEY_SENSITIVE)
    assert sensitive_tag['Value'] == S3_TAG_VALUE_SENSITIVE_TRUE


@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger.S3ResourceUploader')
@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger._create_s3_client')
@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger._config')
def test_tag_s3_version_quarantine_false_sets_sensitive_no(
    mock_config, mock_create_client, mock_uploader_cls
):
    """in_quarantine=False → Sensitive tag value is 'no'."""
    mock_config.get.return_value = 'hdx-test-bucket'
    mock_client = mock.MagicMock()
    mock_create_client.return_value = mock_client
    mock_uploader_cls.return_value.get_path.return_value = 'resources/res-id/file.csv'

    tag_s3_version('res-id', 'file.csv', in_quarantine=False, dataset_name='my-dataset')

    tag_set = mock_client.put_object_tagging.call_args[1]['Tagging']['TagSet']
    sensitive_tag = next(t for t in tag_set if t['Key'] == S3_TAG_KEY_SENSITIVE)
    assert sensitive_tag['Value'] == S3_TAG_VALUE_SENSITIVE_FALSE


# ---------------------------------------------------------------------------
# tag_s3_version – exception wrapping
# ---------------------------------------------------------------------------

@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger.S3ResourceUploader')
@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger._create_s3_client')
@mock.patch('ckanext.hdx_package.helpers.s3_version_tagger._config')
def test_tag_s3_version_raises_s3_exception_on_boto_error(
    mock_config, mock_create_client, mock_uploader_cls
):
    """Any exception from put_object_tagging is re-raised as S3VersionTaggingException."""
    mock_config.get.return_value = 'hdx-test-bucket'
    mock_client = mock.MagicMock()
    mock_client.put_object_tagging.side_effect = Exception('AccessDenied: PutObjectTagging')
    mock_create_client.return_value = mock_client

    with pytest.raises(S3VersionTaggingException, match='AccessDenied'):
        tag_s3_version('res-id', 'file.csv', in_quarantine=True, dataset_name='my-dataset')
