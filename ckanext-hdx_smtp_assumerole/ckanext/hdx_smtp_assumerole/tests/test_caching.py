# -*- coding: utf-8 -*-
"""
Unit tests for get_ses_credentials() and get_credentials_info().

Tests verify:
1. AssumeRole using EC2 instance metadata
2. Correct credential format returned
3. Error handling for various failure scenarios
4. Dogpile caching behavior
5. Credentials info for monitoring
"""
from datetime import datetime, timedelta, timezone

import pytest
import mock
from botocore.exceptions import BotoCoreError, ClientError

from ckanext.hdx_smtp_assumerole.helpers.caching import (
    get_ses_credentials,
    get_credentials_info,
    SESAssumeRoleException
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear dogpile cache before and after each test."""
    get_ses_credentials.invalidate()
    yield
    get_ses_credentials.invalidate()


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn', 'arn:aws:iam::123456789012:role/TestRole')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', 'us-east-1')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.session_name', 'test-session')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.boto3.Session')
def test_successful_assume_role(mock_session_class, mock_fetcher_class, mock_provider_class):
    """Test successful AssumeRole with full ARN."""
    mock_creds = mock.Mock()
    mock_creds.access_key = 'MOCK_ACCESS_KEY'
    mock_creds.secret_key = 'MOCK_SECRET_KEY'
    mock_creds.token = 'MOCK_TOKEN'

    mock_provider = mock.Mock()
    mock_provider.load.return_value = mock_creds
    mock_provider_class.return_value = mock_provider

    expiration_time = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_sts = mock.Mock()
    mock_sts.assume_role.return_value = {
        'Credentials': {
            'AccessKeyId': 'ASSUMED_KEY',
            'SecretAccessKey': 'ASSUMED_SECRET',
            'SessionToken': 'ASSUMED_TOKEN',
            'Expiration': expiration_time
        }
    }

    mock_session = mock.Mock()
    mock_session.client.return_value = mock_sts
    mock_session_class.return_value = mock_session

    credentials = get_ses_credentials()

    assert credentials['access_key'] == 'ASSUMED_KEY'
    assert credentials['secret_key'] == 'ASSUMED_SECRET'
    assert credentials['session_token'] == 'ASSUMED_TOKEN'
    assert credentials['region'] == 'us-east-1'
    assert 'expiration' in credentials

    mock_fetcher_class.assert_called_once_with(timeout=1, num_attempts=2)
    mock_provider.load.assert_called_once()

    mock_sts.assume_role.assert_called_once_with(
        RoleArn='arn:aws:iam::123456789012:role/TestRole',
        RoleSessionName='test-session',
        DurationSeconds=3600
    )


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn', 'TestRole')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', 'us-east-1')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.session_name', 'test-session')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.boto3.Session')
def test_assume_role_with_role_name(mock_session_class, mock_fetcher_class, mock_provider_class):
    """Test AssumeRole when given role name instead of full ARN."""
    mock_creds = mock.Mock()
    mock_creds.access_key = 'MOCK_ACCESS_KEY'
    mock_creds.secret_key = 'MOCK_SECRET_KEY'
    mock_creds.token = 'MOCK_TOKEN'

    mock_provider = mock.Mock()
    mock_provider.load.return_value = mock_creds
    mock_provider_class.return_value = mock_provider

    expiration_time = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_sts = mock.Mock()
    mock_sts.get_caller_identity.return_value = {'Account': '123456789012'}
    mock_sts.assume_role.return_value = {
        'Credentials': {
            'AccessKeyId': 'ASSUMED_KEY',
            'SecretAccessKey': 'ASSUMED_SECRET',
            'SessionToken': 'ASSUMED_TOKEN',
            'Expiration': expiration_time
        }
    }

    mock_session = mock.Mock()
    mock_session.client.return_value = mock_sts
    mock_session_class.return_value = mock_session

    credentials = get_ses_credentials()

    assert credentials['access_key'] == 'ASSUMED_KEY'

    mock_sts.get_caller_identity.assert_called_once()

    mock_sts.assume_role.assert_called_once_with(
        RoleArn='arn:aws:iam::123456789012:role/TestRole',
        RoleSessionName='test-session',
        DurationSeconds=3600
    )


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn', 'TestRole')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', 'us-east-1')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.session_name', 'test-session')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataFetcher')
def test_instance_metadata_failure(mock_fetcher_class, mock_provider_class):
    """Test error handling when instance metadata is unavailable."""
    mock_provider = mock.Mock()
    mock_provider.load.return_value = None
    mock_provider_class.return_value = mock_provider

    with pytest.raises(SESAssumeRoleException) as exc_info:
        get_ses_credentials()

    assert 'Failed to load credentials from EC2 instance metadata' in str(exc_info.value)


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn', None)
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', 'us-east-1')
def test_missing_role_arn_config():
    """Test error when role_arn config is missing."""
    with pytest.raises(SESAssumeRoleException) as exc_info:
        get_ses_credentials()

    assert 'Missing required config' in str(exc_info.value)
    assert 'role_arn' in str(exc_info.value)


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn', 'TestRole')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', None)
def test_missing_region_config():
    """Test error when region config is missing."""
    with pytest.raises(SESAssumeRoleException) as exc_info:
        get_ses_credentials()

    assert 'Missing required config' in str(exc_info.value)
    assert 'region' in str(exc_info.value)


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn', 'arn:aws:iam::123456789012:role/TestRole')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', 'us-east-1')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.session_name', 'test-session')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.boto3.Session')
def test_assume_role_client_error(mock_session_class, mock_fetcher_class, mock_provider_class):
    """Test error handling when AssumeRole returns a ClientError."""
    mock_creds = mock.Mock()
    mock_creds.access_key = 'MOCK_ACCESS_KEY'
    mock_creds.secret_key = 'MOCK_SECRET_KEY'
    mock_creds.token = 'MOCK_TOKEN'

    mock_provider = mock.Mock()
    mock_provider.load.return_value = mock_creds
    mock_provider_class.return_value = mock_provider

    mock_sts = mock.Mock()
    mock_sts.assume_role.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'Not authorized'}},
        'AssumeRole'
    )

    mock_session = mock.Mock()
    mock_session.client.return_value = mock_sts
    mock_session_class.return_value = mock_session

    with pytest.raises(SESAssumeRoleException) as exc_info:
        get_ses_credentials()

    assert 'AccessDenied' in str(exc_info.value)


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn', 'arn:aws:iam::123456789012:role/TestRole')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', 'us-east-1')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.session_name', 'test-session')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.boto3.Session')
def test_assume_role_botocore_error(mock_session_class, mock_fetcher_class, mock_provider_class):
    """Test error handling when BotoCoreError occurs."""
    mock_creds = mock.Mock()
    mock_creds.access_key = 'MOCK_ACCESS_KEY'
    mock_creds.secret_key = 'MOCK_SECRET_KEY'
    mock_creds.token = 'MOCK_TOKEN'

    mock_provider = mock.Mock()
    mock_provider.load.return_value = mock_creds
    mock_provider_class.return_value = mock_provider

    mock_sts = mock.Mock()
    mock_sts.assume_role.side_effect = BotoCoreError()

    mock_session = mock.Mock()
    mock_session.client.return_value = mock_sts
    mock_session_class.return_value = mock_session

    with pytest.raises(SESAssumeRoleException) as exc_info:
        get_ses_credentials()

    assert 'Boto error' in str(exc_info.value)


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn', 'arn:aws:iam::123456789012:role/TestRole')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', 'us-east-1')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.session_name', 'test-session')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.boto3.Session')
def test_assume_role_unexpected_error(mock_session_class, mock_fetcher_class, mock_provider_class):
    """Test error handling when an unexpected error occurs."""
    mock_creds = mock.Mock()
    mock_creds.access_key = 'MOCK_ACCESS_KEY'
    mock_creds.secret_key = 'MOCK_SECRET_KEY'
    mock_creds.token = 'MOCK_TOKEN'

    mock_provider = mock.Mock()
    mock_provider.load.return_value = mock_creds
    mock_provider_class.return_value = mock_provider

    mock_sts = mock.Mock()
    mock_sts.assume_role.side_effect = RuntimeError('Network timeout')

    mock_session = mock.Mock()
    mock_session.client.return_value = mock_sts
    mock_session_class.return_value = mock_session

    with pytest.raises(SESAssumeRoleException) as exc_info:
        get_ses_credentials()

    assert 'Unexpected error' in str(exc_info.value)


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn', 'arn:aws:iam::123456789012:role/TestRole')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', 'us-east-1')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.session_name', 'test-session')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.boto3.Session')
def test_timezone_naive_expiration_converted(mock_session_class, mock_fetcher_class, mock_provider_class):
    """Test that timezone-naive expiration is converted to UTC."""
    mock_creds = mock.Mock()
    mock_creds.access_key = 'MOCK_ACCESS_KEY'
    mock_creds.secret_key = 'MOCK_SECRET_KEY'
    mock_creds.token = 'MOCK_TOKEN'

    mock_provider = mock.Mock()
    mock_provider.load.return_value = mock_creds
    mock_provider_class.return_value = mock_provider

    # Intentionally timezone-naive
    expiration_time = datetime.now() + timedelta(hours=1)
    mock_sts = mock.Mock()
    mock_sts.assume_role.return_value = {
        'Credentials': {
            'AccessKeyId': 'ASSUMED_KEY',
            'SecretAccessKey': 'ASSUMED_SECRET',
            'SessionToken': 'ASSUMED_TOKEN',
            'Expiration': expiration_time
        }
    }

    mock_session = mock.Mock()
    mock_session.client.return_value = mock_sts
    mock_session_class.return_value = mock_session

    credentials = get_ses_credentials()

    assert credentials['expiration'].tzinfo is not None
    assert credentials['expiration'].tzinfo == timezone.utc


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn', 'arn:aws:iam::123456789012:role/TestRole')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', 'us-east-1')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.session_name', 'test-session')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.boto3.Session')
def test_caching_behavior(mock_session_class, mock_fetcher_class, mock_provider_class):
    """Test that dogpile caching works - second call doesn't hit AWS."""
    mock_creds = mock.Mock()
    mock_creds.access_key = 'MOCK_ACCESS_KEY'
    mock_creds.secret_key = 'MOCK_SECRET_KEY'
    mock_creds.token = 'MOCK_TOKEN'

    mock_provider = mock.Mock()
    mock_provider.load.return_value = mock_creds
    mock_provider_class.return_value = mock_provider

    expiration_time = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_sts = mock.Mock()
    mock_sts.assume_role.return_value = {
        'Credentials': {
            'AccessKeyId': 'ASSUMED_KEY',
            'SecretAccessKey': 'ASSUMED_SECRET',
            'SessionToken': 'ASSUMED_TOKEN',
            'Expiration': expiration_time
        }
    }

    mock_session = mock.Mock()
    mock_session.client.return_value = mock_sts
    mock_session_class.return_value = mock_session

    # First call - should hit AWS
    credentials1 = get_ses_credentials()

    # Second call - should use cache
    credentials2 = get_ses_credentials()

    assert credentials1 == credentials2
    assert mock_sts.assume_role.call_count == 1


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.get_ses_credentials')
def test_get_credentials_info_success(mock_get_creds):
    """Test get_credentials_info with valid credentials."""
    expiration = datetime.now(timezone.utc) + timedelta(minutes=45)
    mock_get_creds.return_value = {
        'access_key': 'AKIAIOSFODNN7EXAMPLE',
        'secret_key': 'test-secret',
        'session_token': 'test-token',
        'expiration': expiration,
        'region': 'us-east-1'
    }

    info = get_credentials_info()

    assert info['has_credentials'] is True
    assert info['region'] == 'us-east-1'
    assert info['access_key'] == 'AKIA***MPLE'
    assert 'expiration_time' in info
    assert 'time_until_expiry' in info


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.get_ses_credentials')
def test_get_credentials_info_short_access_key(mock_get_creds):
    """Test get_credentials_info with short access key (no masking)."""
    expiration = datetime.now(timezone.utc) + timedelta(minutes=45)
    mock_get_creds.return_value = {
        'access_key': 'SHORT',
        'secret_key': 'test-secret',
        'session_token': 'test-token',
        'expiration': expiration,
        'region': 'us-east-1'
    }

    info = get_credentials_info()

    assert info['has_credentials'] is True
    assert info['access_key'] == 'SHORT'


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.get_ses_credentials')
def test_get_credentials_info_failure(mock_get_creds):
    """Test get_credentials_info when credentials cannot be loaded."""
    mock_get_creds.side_effect = SESAssumeRoleException('Cannot load credentials')

    info = get_credentials_info()

    assert info['has_credentials'] is False
    assert 'Cannot load credentials' in info['error']


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.get_ses_credentials')
def test_get_credentials_info_naive_expiration(mock_get_creds):
    """Test get_credentials_info handles timezone-naive expiration."""
    expiration = datetime.now() + timedelta(minutes=45)  # Intentionally naive
    mock_get_creds.return_value = {
        'access_key': 'AKIAIOSFODNN7EXAMPLE',
        'secret_key': 'test-secret',
        'session_token': 'test-token',
        'expiration': expiration,
        'region': 'us-east-1'
    }

    info = get_credentials_info()

    assert info['has_credentials'] is True
    assert 'time_until_expiry' in info
