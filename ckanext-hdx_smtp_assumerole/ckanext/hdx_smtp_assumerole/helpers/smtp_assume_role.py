# encoding: utf-8

import logging
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, BotoCoreError
from botocore.credentials import InstanceMetadataProvider, InstanceMetadataFetcher

log = logging.getLogger(__name__)


class SMTPAssumeRoleException(Exception):
    """Exception raised when SMTP AssumeRole operations fail."""
    pass


def create_sts_client_with_instance_profile() -> Any:
    """
    Create STS client using ONLY EC2 instance profile credentials.
    Ignores AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY from environment.

    This is necessary because:
    - Developers need static credentials for S3 in local environments
    - STS AssumeRole calls must use instance profile, not static credentials
    - boto3 prioritizes env vars over instance profile by default

    This function explicitly fetches credentials from EC2 instance metadata,
    bypassing environment variables entirely.

    :return: STS client using instance profile credentials only
    :rtype: boto3.client
    :raises SMTPAssumeRoleException: If instance profile credentials cannot be loaded
    """
    try:
        log.debug('Creating STS client using instance profile credentials (ignoring env vars)')

        # Fetch credentials directly from EC2 instance metadata endpoint
        # This bypasses environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        fetcher = InstanceMetadataFetcher()
        provider = InstanceMetadataProvider(iam_role_fetcher=fetcher)
        credentials = provider.load()

        if credentials is None:
            raise SMTPAssumeRoleException(
                'Failed to load credentials from EC2 instance profile. '
                'Ensure you are running on EC2 with an instance profile attached. '
                'Instance metadata endpoint may be unreachable.'
            )

        log.debug('Successfully loaded credentials from EC2 instance profile')

        # Create STS client with explicit instance profile credentials
        # This ensures env vars (AWS_ACCESS_KEY_ID, etc.) are completely ignored
        sts_client = boto3.client(
            'sts',
            aws_access_key_id=credentials.access_key,
            aws_secret_access_key=credentials.secret_key,
            aws_session_token=credentials.token
        )

        log.debug('Successfully created STS client with instance profile credentials')
        return sts_client

    except SMTPAssumeRoleException:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        msg = f'Failed to create STS client with instance profile: {str(e)}'
        log.error(msg)
        raise SMTPAssumeRoleException(msg)


def get_account_id_from_sts() -> str:
    """
    Get AWS account ID from STS get-caller-identity.
    Uses ONLY EC2 instance profile credentials (ignores env vars).

    :return: AWS account ID
    :rtype: str
    """
    try:
        # Create STS client using instance profile only (ignores AWS_ACCESS_KEY_ID from env)
        sts_client = create_sts_client_with_instance_profile()

        response = sts_client.get_caller_identity()
        account_id = response['Account']
        log.debug(f'Retrieved AWS account ID from instance profile: {account_id}')
        return account_id
    except SMTPAssumeRoleException:
        # Re-raise our custom exceptions
        raise
    except (ClientError, BotoCoreError) as e:
        msg = f'Failed to get AWS account ID from STS: {str(e)}'
        log.error(msg)
        raise SMTPAssumeRoleException(msg)


def build_role_arn(role_name_or_arn: str, region: Optional[str] = None) -> str:
    """
    Build full role ARN from role name or return ARN if already provided.
    If only role name is provided, account ID is deduced from STS.

    :param role_name_or_arn: Role name (e.g., 'my-role') or full ARN
    :type role_name_or_arn: str
    :param region: AWS region (optional, for logging)
    :type region: str
    :return: Full role ARN
    :rtype: str
    """
    if not role_name_or_arn:
        raise SMTPAssumeRoleException('Role name or ARN is required')

    # Check if already an ARN
    if role_name_or_arn.startswith('arn:aws:iam::'):
        log.debug(f'Using provided role ARN: {role_name_or_arn}')
        return role_name_or_arn

    # Build ARN from role name
    account_id = get_account_id_from_sts()
    role_arn = f'arn:aws:iam::{account_id}:role/{role_name_or_arn}'
    log.debug(f'Built role ARN: {role_arn}')
    return role_arn


def assume_role_for_smtp(role_name_or_arn: str, region: str, session_name: str = 'ckan-ses-session', duration_seconds: int = 3600) -> Dict[str, Any]:
    """
    Assume AWS IAM role and return temporary credentials for SES API.
    Uses ONLY EC2 instance profile credentials (ignores env vars).

    This function:
    1. Builds full role ARN (deduces account ID if needed)
    2. Assumes the role using STS with instance profile only
    3. Returns temporary credentials (access_key, secret_key, session_token)

    Note: This function explicitly uses instance profile credentials and ignores
    AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY from environment. This allows
    using static credentials for other services (like S3) without interfering
    with STS AssumeRole calls.

    The returned credentials are used with SES API (not SMTP), which supports
    session tokens from temporary credentials.

    :param role_name_or_arn: Role name or full ARN to assume
    :type role_name_or_arn: str
    :param region: AWS region for SES API
    :type region: str
    :param session_name: Session name for AssumeRole (default: 'ckan-ses-session')
    :type session_name: str
    :param duration_seconds: Duration of temporary credentials (default: 3600)
    :type duration_seconds: int
    :return: Dictionary with access_key, secret_key, session_token, expiration
    :rtype: dict
    """
    try:
        # Build role ARN
        role_arn = build_role_arn(role_name_or_arn, region)

        # Create STS client using instance profile only (ignores AWS_ACCESS_KEY_ID from env)
        sts_client = create_sts_client_with_instance_profile()
        log.debug(f'Assuming role: {role_arn} with session: {session_name}')

        response = sts_client.assume_role(
            RoleArn=role_arn,
            RoleSessionName=session_name,
            DurationSeconds=duration_seconds
        )

        credentials = response['Credentials']
        access_key = credentials['AccessKeyId']
        secret_key = credentials['SecretAccessKey']
        session_token = credentials['SessionToken']
        expiration = credentials['Expiration']

        log.debug(f'Successfully assumed role for SES API. Credentials expire at: {expiration}')

        return {
            'access_key': access_key,
            'secret_key': secret_key,
            'session_token': session_token,
            'expiration': expiration,
        }

    except SMTPAssumeRoleException:
        # Re-raise our custom exceptions
        raise
    except (ClientError, BotoCoreError) as e:
        msg = f'Failed to assume role for SMTP: {str(e)}'
        log.error(msg)
        raise SMTPAssumeRoleException(msg)
    except Exception as e:
        msg = f'Unexpected error during SMTP AssumeRole: {str(e)}'
        log.error(msg)
        raise SMTPAssumeRoleException(msg)
