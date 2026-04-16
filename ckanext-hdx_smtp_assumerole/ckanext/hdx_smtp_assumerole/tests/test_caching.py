# -*- coding: utf-8 -*-
"""
Unit tests for get_cached_ses_credentials() and get_credentials_info().

The full AssumeRole logic and dogpile caching behaviour are tested in
ckanext-hdx_theme's test_aws_credentials.py.
Here we test only what is specific to this module:
  1. Config validation (missing role_arn / region raises before hitting AWS)
  2. That get_cached_aws_credentials is called with the correct SES config values
  3. get_credentials_info() helper behaviour
  4. SESAssumeRoleException is an alias for AwsAssumeRoleException
"""
from datetime import datetime, timedelta, timezone
from unittest import mock

import pytest

from ckanext.hdx_theme.helpers.aws_credentials import AwsAssumeRoleException
from ckanext.hdx_smtp_assumerole.helpers.caching import (
    SESAssumeRoleException,
    get_cached_ses_credentials,
    get_credentials_info,
)

_FAKE_CREDS = {
    'access_key': 'KEY', 'secret_key': 'SECRET', 'session_token': 'TOKEN',
    'expiration': datetime.now(timezone.utc) + timedelta(hours=1),
    'region': 'us-east-1',
}


# ---------------------------------------------------------------------------
# get_cached_ses_credentials
# ---------------------------------------------------------------------------

@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn',
            'arn:aws:iam::123456789012:role/SESRole')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', 'us-east-1')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.session_name', 'ckan-ses-session')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.get_cached_aws_credentials')
def test_delegates_to_shared_cache_with_ses_config(mock_cached):
    """get_cached_ses_credentials passes its SES config to get_cached_aws_credentials."""
    mock_cached.return_value = _FAKE_CREDS

    result = get_cached_ses_credentials()

    mock_cached.assert_called_once_with(
        'arn:aws:iam::123456789012:role/SESRole',
        'us-east-1',
        'ckan-ses-session',
    )
    assert result == _FAKE_CREDS


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn', None)
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', 'us-east-1')
def test_missing_role_arn_raises_before_aws_call():
    with pytest.raises(SESAssumeRoleException, match='role_arn'):
        get_cached_ses_credentials()


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.role_name_or_arn',
            'arn:aws:iam::123456789012:role/SESRole')
@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.region', None)
def test_missing_region_raises_before_aws_call():
    with pytest.raises(SESAssumeRoleException, match='region'):
        get_cached_ses_credentials()


# ---------------------------------------------------------------------------
# SESAssumeRoleException alias
# ---------------------------------------------------------------------------

def test_ses_exception_is_alias_for_aws_exception():
    assert SESAssumeRoleException is AwsAssumeRoleException


def test_smtp_assume_role_shim_exception_is_alias_for_aws_exception():
    from ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role import SMTPAssumeRoleException
    assert SMTPAssumeRoleException is AwsAssumeRoleException


# ---------------------------------------------------------------------------
# get_credentials_info
# ---------------------------------------------------------------------------

@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.get_cached_ses_credentials')
def test_credentials_info_success(mock_get_creds):
    expiration = datetime.now(timezone.utc) + timedelta(minutes=45)
    mock_get_creds.return_value = {
        'access_key': 'AKIAIOSFODNN7EXAMPLE',
        'secret_key': 'secret', 'session_token': 'token',
        'expiration': expiration, 'region': 'us-east-1',
    }

    info = get_credentials_info()

    assert info['has_credentials'] is True
    assert info['region'] == 'us-east-1'
    assert info['access_key'] == 'AKIA***MPLE'
    assert 'expiration_time' in info
    assert 'time_until_expiry' in info


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.get_cached_ses_credentials')
def test_credentials_info_short_key_not_masked(mock_get_creds):
    expiration = datetime.now(timezone.utc) + timedelta(minutes=45)
    mock_get_creds.return_value = {
        'access_key': 'SHORT', 'secret_key': 'secret', 'session_token': 'token',
        'expiration': expiration, 'region': 'us-east-1',
    }
    assert get_credentials_info()['access_key'] == 'SHORT'


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.get_cached_ses_credentials')
def test_credentials_info_failure_returns_error_dict(mock_get_creds):
    mock_get_creds.side_effect = SESAssumeRoleException('Cannot load credentials')
    info = get_credentials_info()
    assert info['has_credentials'] is False
    assert 'Cannot load credentials' in info['error']


@mock.patch('ckanext.hdx_smtp_assumerole.helpers.caching.get_cached_ses_credentials')
def test_credentials_info_naive_expiration_handled(mock_get_creds):
    expiration = datetime.now() + timedelta(minutes=45)  # intentionally naive
    mock_get_creds.return_value = {
        'access_key': 'AKIAIOSFODNN7EXAMPLE', 'secret_key': 'secret',
        'session_token': 'token', 'expiration': expiration, 'region': 'us-east-1',
    }
    info = get_credentials_info()
    assert info['has_credentials'] is True
    assert 'time_until_expiry' in info
