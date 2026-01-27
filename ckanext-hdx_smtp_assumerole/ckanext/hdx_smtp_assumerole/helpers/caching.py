# encoding: utf-8

import logging
from datetime import datetime, timezone

import boto3
from botocore.credentials import InstanceMetadataProvider, InstanceMetadataFetcher
from botocore.exceptions import BotoCoreError, ClientError

import ckan.plugins.toolkit as tk

from dogpile.cache import make_region
from ckanext.hdx_theme.helpers.caching import dogpile_standard_config, dogpile_config_filter

log = logging.getLogger(__name__)
config = tk.config

dogpile_ses_config = {
    'cache.redis.expiration_time': 60 * 55,  # 55 minutes, 5 minutes before credentials expire
}
dogpile_ses_config.update(dogpile_standard_config)

dogpile_ses_region = make_region(key_mangler=lambda key: 'ses-' + key)
dogpile_ses_region.configure_from_config(dogpile_ses_config, dogpile_config_filter)

# Load AWS configuration at module import time
# Note: This is intentional and safe because:
# 1. CKAN config is fully loaded before plugins are imported
# 2. These values don't change at runtime (require app restart)
# 3. Loading once at import avoids repeated config lookups on every request
role_name_or_arn = config.get('ckanext.hdx_smtp_assumerole.role_arn')
region = config.get('ckanext.hdx_smtp_assumerole.region')
session_name = config.get('ckanext.hdx_smtp_assumerole.session_name', 'ckan-ses-session')

log.info(f'SES Caching Config - role_arn: {role_name_or_arn}, region: {region}, session_name: {session_name}')


class SESAssumeRoleException(Exception):
    """Exception raised when AssumeRole fails"""
    pass


@dogpile_ses_region.cache_on_arguments()
def get_ses_credentials():
    """
    Load fresh SES credentials via AssumeRole using EC2 instance metadata.
    Cached in Redis via dogpile - automatically reuses credentials if valid.

    Uses configuration from:
    - ckanext.hdx_smtp_assumerole.role_arn
    - ckanext.hdx_smtp_assumerole.region
    - ckanext.hdx_smtp_assumerole.session_name

    :return: Dict with credentials (access_key, secret_key, session_token, expiration, region)
    :raises SESAssumeRoleException: If credential loading fails
    """
    try:
        # Validate configuration
        if not role_name_or_arn:
            raise SESAssumeRoleException('Missing required config: ckanext.hdx_smtp_assumerole.role_arn')
        if not region:
            raise SESAssumeRoleException('Missing required config: ckanext.hdx_smtp_assumerole.region')

        log.info(f'Loading fresh SES credentials via AssumeRole for role: {role_name_or_arn}')

        # Create base session with explicit instance metadata provider
        fetcher = InstanceMetadataFetcher(timeout=1, num_attempts=2)
        provider = InstanceMetadataProvider(iam_role_fetcher=fetcher)

        # Get credentials from instance metadata
        instance_creds = provider.load()
        if instance_creds is None:
            raise SESAssumeRoleException('Failed to load credentials from EC2 instance metadata')

        # Create session with instance profile credentials
        base_session = boto3.Session(
            aws_access_key_id=instance_creds.access_key,
            aws_secret_access_key=instance_creds.secret_key,
            aws_session_token=instance_creds.token,
            region_name=region
        )

        sts_client = base_session.client('sts')

        # Check if role_arn is full ARN or just role name
        if role_name_or_arn.startswith('arn:aws:iam::'):
            full_role_arn = role_name_or_arn
        else:
            account_id = sts_client.get_caller_identity()['Account']
            full_role_arn = f'arn:aws:iam::{account_id}:role/{role_name_or_arn}'

        log.info(f'Assuming role with ARN: {full_role_arn}')
        log.info(f'Using session name: {session_name}')
        log.info(f'Using region: {region}')

        # Credentials are valid for 60 minutes (DurationSeconds=3600).
        # Dogpile expires the cached value after 55 minutes, so the next request
        # triggers regeneration with at least 5 minutes of validity remaining.
        assumed_role = sts_client.assume_role(
            RoleArn=full_role_arn,
            RoleSessionName=session_name,
            DurationSeconds=3600  # 60 minutes = 3600 seconds
        )

        # Extract credentials - use same keys as ses_sender expects
        credentials = {
            'access_key': assumed_role['Credentials']['AccessKeyId'],
            'secret_key': assumed_role['Credentials']['SecretAccessKey'],
            'session_token': assumed_role['Credentials']['SessionToken'],
            'expiration': assumed_role['Credentials']['Expiration'],
            'region': region
        }

        # Ensure expiration is timezone-aware
        if credentials['expiration'].tzinfo is None:
            credentials['expiration'] = credentials['expiration'].replace(tzinfo=timezone.utc)

        # Calculate time until expiration
        now = datetime.now(timezone.utc)
        time_until_expiry = credentials['expiration'] - now
        minutes_until_expiry = int(time_until_expiry.total_seconds() / 60)

        expiration_str = credentials['expiration'].strftime('%Y-%m-%d %H:%M:%S UTC')
        log.info(f'Successfully loaded SES credentials, expire at: {expiration_str} (in {minutes_until_expiry} minutes)')

        return credentials

    except SESAssumeRoleException:
        raise
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        log.error(f'AWS API error during AssumeRole: {error_code} - {error_msg}')
        raise SESAssumeRoleException(f'AWS API error: {error_code} - {error_msg}')
    except BotoCoreError as e:
        log.error(f'Boto core error loading credentials: {e}')
        raise SESAssumeRoleException(f'Boto error: {e}')
    except Exception as e:
        # Catch-all for unexpected errors (e.g., network issues, serialization problems)
        log.error(f'Unexpected error loading SES credentials: {e}', exc_info=True)
        raise SESAssumeRoleException(f'Unexpected error: {e}')


def get_credentials_info():
    """
    Get information about current credentials (for debugging/monitoring).

    :return: Dict with credentials info
    :rtype: dict
    """
    try:
        credentials = get_ses_credentials()

        now = datetime.now(timezone.utc)
        expiration = credentials['expiration']
        if expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=timezone.utc)

        time_until_expiry = expiration - now

        # Mask access key for security
        access_key = credentials.get('access_key', 'N/A')
        if len(access_key) > 8:
            masked_key = f"{access_key[:4]}***{access_key[-4:]}"
        else:
            masked_key = access_key

        return {
            'has_credentials': True,
            'expiration_time': str(expiration),
            'time_until_expiry': str(time_until_expiry),
            'region': credentials.get('region'),
            'access_key': masked_key
        }
    except SESAssumeRoleException as e:
        return {
            'has_credentials': False,
            'error': str(e)
        }
