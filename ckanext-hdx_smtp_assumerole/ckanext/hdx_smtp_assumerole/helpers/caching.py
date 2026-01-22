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

# Debug logging
log.info('SES Caching Config - role_arn: {0}, region: {1}, session_name: {2}'.format(
    role_name_or_arn, region, session_name))


class SESAssumeRoleException(Exception):
    """Exception raised when AssumeRole fails"""
    pass


@dogpile_ses_region.cache_on_arguments()
def cached_load_ses_credentials():
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

        log.info('Loading fresh SES credentials via AssumeRole for role: {0}'.format(role_name_or_arn))

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
            full_role_arn = 'arn:aws:iam::{0}:role/{1}'.format(account_id, role_name_or_arn)

        log.info('Assuming role with ARN: {0}'.format(full_role_arn))
        log.info('Using session name: {0}'.format(session_name))
        log.info('Using region: {0}'.format(region))

        # Assume role with 1 hour duration (credentials valid for 60 minutes)
        # Cache TTL is 55 minutes, so cached credentials are only used for 55 minutes
        # and are refreshed 5 minutes before they actually expire
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

        log.info('Successfully loaded SES credentials, expire at: {0} (in {1} minutes)'.format(
            credentials['expiration'].strftime('%Y-%m-%d %H:%M:%S UTC'),
            minutes_until_expiry))

        return credentials

    except SESAssumeRoleException:
        raise
    except ClientError as e:
        error_code = e.response.get('Error', {}).get('Code', 'Unknown')
        error_msg = e.response.get('Error', {}).get('Message', str(e))
        log.error('AWS API error during AssumeRole: {0} - {1}'.format(error_code, error_msg))
        raise SESAssumeRoleException('AWS API error: {0} - {1}'.format(error_code, error_msg))
    except BotoCoreError as e:
        log.error('Boto core error loading credentials: {0}'.format(str(e)))
        raise SESAssumeRoleException('Boto error: {0}'.format(str(e)))
    except Exception as e:
        # Catch-all for unexpected errors (e.g., network issues, serialization problems)
        log.error('Unexpected error loading SES credentials: {0}'.format(str(e)), exc_info=True)
        raise SESAssumeRoleException('Unexpected error: {0}'.format(str(e)))
