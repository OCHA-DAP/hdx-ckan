# -*- coding: utf-8 -*-
"""
Unit tests for assume_role_with_instance_profile() and get_cached_aws_credentials().

This is the single place that exercises the full boto3/botocore call chain.
Plugin-level caching modules (s3filestore, hdx_smtp_assumerole) mock
get_cached_aws_credentials directly instead of duplicating these tests.
"""
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest
from botocore.exceptions import BotoCoreError, ClientError

from ckanext.hdx_theme.helpers.aws_credentials import (
    AwsAssumeRoleException,
    assume_role_with_instance_profile,
    get_cached_aws_credentials,
    get_credentials_info,
)

_FULL_ARN = 'arn:aws:iam::123456789012:role/TestRole'
_REGION = 'us-east-1'
_SESSION = 'test-session'


@pytest.fixture(autouse=True)
def clear_cache():
    get_cached_aws_credentials.invalidate(_FULL_ARN, _REGION, _SESSION)
    yield
    get_cached_aws_credentials.invalidate(_FULL_ARN, _REGION, _SESSION)


def _mock_instance_creds():
    creds = mock.Mock()
    creds.access_key = 'INSTANCE_KEY'
    creds.secret_key = 'INSTANCE_SECRET'
    creds.token = 'INSTANCE_TOKEN'
    return creds


def _mock_sts(expiration, account_id=None):
    sts = mock.Mock()
    sts.assume_role.return_value = {
        'Credentials': {
            'AccessKeyId': 'ASSUMED_KEY',
            'SecretAccessKey': 'ASSUMED_SECRET',
            'SessionToken': 'ASSUMED_TOKEN',
            'Expiration': expiration,
        }
    }
    if account_id:
        sts.get_caller_identity.return_value = {'Account': account_id}
    return sts


# ---------------------------------------------------------------------------
# assume_role_with_instance_profile – core logic
# ---------------------------------------------------------------------------

@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.boto3.Session')
def test_full_arn_does_not_call_get_caller_identity(mock_session_cls, mock_fetcher_cls, mock_provider_cls):
    """Full ARN: STS AssumeRole called directly, get_caller_identity skipped."""
    mock_provider_cls.return_value.load.return_value = _mock_instance_creds()
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_sts = _mock_sts(expiration)
    mock_session_cls.return_value.client.return_value = mock_sts

    result = assume_role_with_instance_profile(_FULL_ARN, _REGION, _SESSION)

    assert result['access_key'] == 'ASSUMED_KEY'
    assert result['secret_key'] == 'ASSUMED_SECRET'
    assert result['session_token'] == 'ASSUMED_TOKEN'
    assert result['region'] == _REGION
    assert result['expiration'].tzinfo is not None
    mock_sts.get_caller_identity.assert_not_called()
    mock_fetcher_cls.assert_called_once_with(timeout=1, num_attempts=2)
    mock_sts.assume_role.assert_called_once_with(
        RoleArn=_FULL_ARN,
        RoleSessionName=_SESSION,
        DurationSeconds=3600,
    )


@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.boto3.Session')
def test_bare_role_name_resolves_account_id(mock_session_cls, mock_fetcher_cls, mock_provider_cls):
    """Bare role name: account ID is resolved via get_caller_identity."""
    mock_provider_cls.return_value.load.return_value = _mock_instance_creds()
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_sts = _mock_sts(expiration, account_id='123456789012')
    mock_session_cls.return_value.client.return_value = mock_sts

    result = assume_role_with_instance_profile('TestRole', _REGION, _SESSION)

    assert result['access_key'] == 'ASSUMED_KEY'
    mock_sts.get_caller_identity.assert_called_once()
    mock_sts.assume_role.assert_called_once_with(
        RoleArn=_FULL_ARN,
        RoleSessionName=_SESSION,
        DurationSeconds=3600,
    )


@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.boto3.Session')
def test_custom_duration_forwarded(mock_session_cls, mock_fetcher_cls, mock_provider_cls):
    mock_provider_cls.return_value.load.return_value = _mock_instance_creds()
    mock_sts = _mock_sts(datetime.now(timezone.utc) + timedelta(hours=2))
    mock_session_cls.return_value.client.return_value = mock_sts

    assume_role_with_instance_profile(_FULL_ARN, _REGION, _SESSION, duration_seconds=7200)

    mock_sts.assume_role.assert_called_once_with(
        RoleArn=_FULL_ARN, RoleSessionName=_SESSION, DurationSeconds=7200
    )


@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataFetcher')
def test_instance_metadata_unavailable_raises(mock_fetcher_cls, mock_provider_cls):
    mock_provider_cls.return_value.load.return_value = None
    with pytest.raises(AwsAssumeRoleException, match='instance metadata'):
        assume_role_with_instance_profile(_FULL_ARN, _REGION, _SESSION)


@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.boto3.Session')
def test_client_error_wrapped(mock_session_cls, mock_fetcher_cls, mock_provider_cls):
    mock_provider_cls.return_value.load.return_value = _mock_instance_creds()
    mock_sts = mock.Mock()
    mock_sts.assume_role.side_effect = ClientError(
        {'Error': {'Code': 'AccessDenied', 'Message': 'Not authorized'}}, 'AssumeRole'
    )
    mock_session_cls.return_value.client.return_value = mock_sts
    with pytest.raises(AwsAssumeRoleException, match='AccessDenied'):
        assume_role_with_instance_profile(_FULL_ARN, _REGION, _SESSION)


@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.boto3.Session')
def test_botocore_error_wrapped(mock_session_cls, mock_fetcher_cls, mock_provider_cls):
    mock_provider_cls.return_value.load.return_value = _mock_instance_creds()
    mock_sts = mock.Mock()
    mock_sts.assume_role.side_effect = BotoCoreError()
    mock_session_cls.return_value.client.return_value = mock_sts
    with pytest.raises(AwsAssumeRoleException, match='Boto error'):
        assume_role_with_instance_profile(_FULL_ARN, _REGION, _SESSION)


@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.boto3.Session')
def test_unexpected_error_wrapped(mock_session_cls, mock_fetcher_cls, mock_provider_cls):
    mock_provider_cls.return_value.load.return_value = _mock_instance_creds()
    mock_sts = mock.Mock()
    mock_sts.assume_role.side_effect = RuntimeError('network timeout')
    mock_session_cls.return_value.client.return_value = mock_sts
    with pytest.raises(AwsAssumeRoleException, match='Unexpected error'):
        assume_role_with_instance_profile(_FULL_ARN, _REGION, _SESSION)


@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataProvider')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.InstanceMetadataFetcher')
@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.boto3.Session')
def test_timezone_naive_expiration_normalised(mock_session_cls, mock_fetcher_cls, mock_provider_cls):
    mock_provider_cls.return_value.load.return_value = _mock_instance_creds()
    naive = datetime.now() + timedelta(hours=1)
    mock_sts = mock.Mock()
    mock_sts.assume_role.return_value = {
        'Credentials': {
            'AccessKeyId': 'K', 'SecretAccessKey': 'S',
            'SessionToken': 'T', 'Expiration': naive,
        }
    }
    mock_session_cls.return_value.client.return_value = mock_sts

    result = assume_role_with_instance_profile(_FULL_ARN, _REGION, _SESSION)

    assert result['expiration'].tzinfo == timezone.utc


# ---------------------------------------------------------------------------
# get_cached_aws_credentials – validation (no Redis required: validation fires
# in the wrapper before dogpile generates a key or touches the backend)
# ---------------------------------------------------------------------------

def test_missing_role_raises_before_aws_call():
    with pytest.raises(AwsAssumeRoleException, match='role_name_or_arn'):
        get_cached_aws_credentials('', _REGION, _SESSION)


def test_missing_region_raises_before_aws_call():
    with pytest.raises(AwsAssumeRoleException, match='region'):
        get_cached_aws_credentials(_FULL_ARN, '', _SESSION)


def test_missing_session_name_raises_before_aws_call():
    with pytest.raises(AwsAssumeRoleException, match='session_name'):
        get_cached_aws_credentials(_FULL_ARN, _REGION, '')


def test_whitespace_session_name_raises_before_aws_call():
    with pytest.raises(AwsAssumeRoleException, match='session_name'):
        get_cached_aws_credentials(_FULL_ARN, _REGION, '   ')


def test_whitespace_role_raises_before_aws_call():
    with pytest.raises(AwsAssumeRoleException, match='role_name_or_arn'):
        get_cached_aws_credentials('   ', _REGION, _SESSION)


def test_whitespace_region_raises_before_aws_call():
    with pytest.raises(AwsAssumeRoleException, match='region'):
        get_cached_aws_credentials(_FULL_ARN, '   ', _SESSION)


# ---------------------------------------------------------------------------
# get_cached_aws_credentials – caching behaviour (dogpile cache backends)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# get_credentials_info – generic helper
# ---------------------------------------------------------------------------

def test_credentials_info_success():
    expiration = datetime.now(timezone.utc) + timedelta(minutes=45)
    creds = {
        'access_key': 'AKIAIOSFODNN7EXAMPLE', 'secret_key': 'secret',
        'session_token': 'token', 'expiration': expiration, 'region': 'us-east-1',
    }
    info = get_credentials_info(lambda: creds)
    assert info['has_credentials'] is True
    assert info['region'] == 'us-east-1'
    assert info['access_key'] == 'AKIA***MPLE'
    assert 'expiration_time' in info
    assert 'time_until_expiry' in info


def test_credentials_info_short_key_not_masked():
    expiration = datetime.now(timezone.utc) + timedelta(minutes=45)
    creds = {
        'access_key': 'SHORT', 'secret_key': 'secret',
        'session_token': 'token', 'expiration': expiration, 'region': 'us-east-1',
    }
    assert get_credentials_info(lambda: creds)['access_key'] == 'SHORT'


def test_credentials_info_failure_returns_error_dict():
    def failing():
        raise AwsAssumeRoleException('Cannot load credentials')
    info = get_credentials_info(failing)
    assert info['has_credentials'] is False
    assert 'Cannot load credentials' in info['error']


def test_credentials_info_non_aws_exception_handled():
    """Non-AwsAssumeRoleException (e.g. Redis ConnectionError) is also caught."""
    def failing():
        raise ConnectionError('Redis connection refused')
    info = get_credentials_info(failing)
    assert info['has_credentials'] is False
    assert 'Redis connection refused' in info['error']


def test_credentials_info_naive_expiration_handled():
    expiration = datetime.now() + timedelta(minutes=45)  # intentionally naive
    creds = {
        'access_key': 'AKIAIOSFODNN7EXAMPLE', 'secret_key': 'secret',
        'session_token': 'token', 'expiration': expiration, 'region': 'us-east-1',
    }
    info = get_credentials_info(lambda: creds)
    assert info['has_credentials'] is True
    assert 'time_until_expiry' in info


@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.assume_role_with_instance_profile')
def test_cached_function_caches_result(mock_assume):
    """Second call with same args returns cached result, does not call assume_role again."""
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_assume.return_value = {
        'access_key': 'KEY', 'secret_key': 'SECRET', 'session_token': 'TOKEN',
        'expiration': expiration, 'region': _REGION,
    }

    result1 = get_cached_aws_credentials(_FULL_ARN, _REGION, _SESSION)
    result2 = get_cached_aws_credentials(_FULL_ARN, _REGION, _SESSION)

    assert result1 == result2
    assert mock_assume.call_count == 1


@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.assume_role_with_instance_profile')
def test_different_args_produce_independent_cache_entries(mock_assume):
    """Different session_names produce separate cache entries (S3 vs SES isolation)."""
    get_cached_aws_credentials.invalidate(_FULL_ARN, _REGION, 'ckan-s3-session')
    get_cached_aws_credentials.invalidate(_FULL_ARN, _REGION, 'ckan-ses-session')

    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_assume.return_value = {
        'access_key': 'KEY', 'secret_key': 'SECRET', 'session_token': 'TOKEN',
        'expiration': expiration, 'region': _REGION,
    }

    get_cached_aws_credentials(_FULL_ARN, _REGION, 'ckan-s3-session')
    get_cached_aws_credentials(_FULL_ARN, _REGION, 'ckan-ses-session')

    assert mock_assume.call_count == 2  # each unique tuple hit AWS once


@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.assume_role_with_instance_profile')
def test_whitespace_args_produce_same_cache_entry(mock_assume):
    """
    Callers passing padded and unpadded variants of the same (role, region,
    session) tuple should hit the same cache entry. Validates that the
    normalization in get_cached_aws_credentials is applied consistently.
    """
    get_cached_aws_credentials.invalidate(_FULL_ARN, _REGION, _SESSION)

    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_assume.return_value = {
        'access_key': 'KEY', 'secret_key': 'SECRET', 'session_token': 'TOKEN',
        'expiration': expiration, 'region': _REGION,
    }

    get_cached_aws_credentials(_FULL_ARN, _REGION, _SESSION)
    get_cached_aws_credentials(f'  {_FULL_ARN}  ', f'  {_REGION}  ', f'  {_SESSION}  ')

    assert mock_assume.call_count == 1  # padded variant hit the same cache entry


@mock.patch('ckanext.hdx_theme.helpers.aws_credentials.assume_role_with_instance_profile')
def test_invalidate_normalizes_args(mock_assume):
    """
    invalidate() must apply the same normalization as get_cached_aws_credentials,
    otherwise callers passing unstripped values would silently miss the cache
    entry they intended to remove.
    """
    expiration = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_assume.return_value = {
        'access_key': 'KEY', 'secret_key': 'SECRET', 'session_token': 'TOKEN',
        'expiration': expiration, 'region': _REGION,
    }

    # Populate cache with canonical args
    get_cached_aws_credentials(_FULL_ARN, _REGION, _SESSION)
    assert mock_assume.call_count == 1

    # Invalidate using padded args – must still hit the canonical entry
    get_cached_aws_credentials.invalidate(
        f'  {_FULL_ARN}  ', f'  {_REGION}  ', f'  {_SESSION}  '
    )

    # Next call should regenerate the credentials (cache was really invalidated)
    get_cached_aws_credentials(_FULL_ARN, _REGION, _SESSION)
    assert mock_assume.call_count == 2
