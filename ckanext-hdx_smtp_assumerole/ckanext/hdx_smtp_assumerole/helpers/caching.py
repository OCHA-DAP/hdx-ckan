# encoding: utf-8

import logging

import ckan.plugins.toolkit as tk

from ckanext.hdx_theme.helpers.aws_credentials import (
    AwsAssumeRoleException,
    get_cached_aws_credentials,
    get_credentials_info as _get_credentials_info_core,
)

log = logging.getLogger(__name__)
config = tk.config

# Load SES configuration at module import time.
# CKAN config is fully loaded before plugins are imported, so this is safe.
role_name_or_arn = config.get('ckanext.hdx_smtp_assumerole.role_arn')
region = config.get('ckanext.hdx_smtp_assumerole.region')
session_name = config.get(
    'ckanext.hdx_smtp_assumerole.session_name', 'ckan-ses-session'
)

log.info('SES credentials config - role_arn: %s, region: %s, session_name: %s',
         role_name_or_arn, region, session_name)

# Alias so existing code inside this plugin can catch SESAssumeRoleException
# without importing AwsAssumeRoleException directly.
SESAssumeRoleException = AwsAssumeRoleException


def get_cached_ses_credentials():
    """
    Return temporary SES credentials via AssumeRole, cached in Redis via dogpile.

    Thin wrapper around ``get_cached_aws_credentials`` from ckanext-hdx_theme.
    Reads SES-specific config (``ckanext.hdx_smtp_assumerole.*``) and delegates
    caching to the shared dogpile region in hdx_theme.

    Because the session_name (``'ckan-ses-session'``) differs from the S3
    session name, the Redis cache key is independent of S3 credentials even
    though both use the same underlying dogpile region.

    :return: Dict with keys access_key, secret_key, session_token, expiration, region
    :raises SESAssumeRoleException: If credential loading or config validation fails
    """
    if not role_name_or_arn:
        raise SESAssumeRoleException(
            'Missing required config: ckanext.hdx_smtp_assumerole.role_arn'
        )
    if not region:
        raise SESAssumeRoleException(
            'Missing required config: ckanext.hdx_smtp_assumerole.region'
        )

    return get_cached_aws_credentials(role_name_or_arn, region, session_name)


def get_credentials_info():
    """
    Return information about the current SES credentials (for debugging/monitoring).

    Delegates to the generic helper in ``ckanext.hdx_theme.helpers.aws_credentials``.

    :return: Dict with has_credentials, expiration_time, time_until_expiry, region, access_key
    :rtype: dict
    """
    return _get_credentials_info_core(get_cached_ses_credentials)
