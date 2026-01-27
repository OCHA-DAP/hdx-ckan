# encoding: utf-8

import logging
import re
from typing import Dict, Any
import ckan.plugins as plugins
import ckan.plugins.toolkit as tk

from ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role import SMTPAssumeRoleException
from ckanext.hdx_smtp_assumerole.helpers.caching import (
    get_ses_credentials,
    get_credentials_info,
    SESAssumeRoleException
)
from ckanext.hdx_smtp_assumerole.helpers.mailer_patches import patch_mailer_functions
from ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches import patch_hdx_users_mailer

log = logging.getLogger(__name__)


def _validate_region(region: str) -> None:
    """
    Validate AWS region format.

    :param region: AWS region string
    :raises SMTPAssumeRoleException: If region format is invalid
    """
    # Check for empty/whitespace-only string first for clearer error message
    if not region or not region.strip():
        raise SMTPAssumeRoleException('AWS region cannot be empty')

    # Common AWS regions - not exhaustive but covers most cases
    # Format: prefix-region-number (e.g., us-east-1, eu-west-2)
    # Supports hyphenated region names (e.g., us-gov-west-1, ap-northeast-3)
    # Pattern ensures: exactly 2 letter prefix, at least 2 letters between dashes, no consecutive dashes
    valid_region_pattern = r'^[a-z]{2}-[a-z]{2,}(-[a-z]{2,})*-\d+$'

    if not re.match(valid_region_pattern, region):
        raise SMTPAssumeRoleException(
            f'Invalid AWS region format: {region}. '
            f'Expected format like "us-east-1" or "eu-west-2"'
        )


def _validate_role_arn(role_arn: str) -> None:
    """
    Validate IAM role ARN or role name format.

    :param role_arn: Role ARN or role name
    :raises SMTPAssumeRoleException: If format is invalid
    """
    # Check for empty/whitespace-only string first for clearer error message
    if not role_arn or not role_arn.strip():
        raise SMTPAssumeRoleException('IAM role ARN or name cannot be empty')

    # If it starts with 'arn:', validate full ARN format
    if role_arn.startswith('arn:'):
        # ARN format: arn:aws:iam::123456789012:role/RoleName or arn:aws:iam::123456789012:role/path/RoleName
        arn_pattern = r'^arn:aws:iam::\d{12}:role/[\w+=,.@/-]+$'
        if not re.match(arn_pattern, role_arn):
            raise SMTPAssumeRoleException(
                f'Invalid IAM role ARN format: {role_arn}. '
                f'Expected format: arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME or arn:aws:iam::ACCOUNT_ID:role/path/ROLE_NAME'
            )
    else:
        # Validate role name format (alphanumeric + special chars allowed by IAM)
        role_name_pattern = r'^[\w+=,.@-]+$'
        if not re.match(role_name_pattern, role_arn):
            raise SMTPAssumeRoleException(
                f'Invalid IAM role name: {role_arn}. '
                f'Role names can contain alphanumeric characters and: + = , . @ -'
            )


def run_on_startup(config: Dict[str, Any]) -> None:
    """
    Run startup tasks for SMTP AssumeRole plugin.

    If AssumeRole is enabled, this will:
    1. Initialize the credentials manager with config
    2. Load initial credentials via AssumeRole
    3. Apply monkey patches to email senders to use SES API
    4. Set up email domain defaults if configured

    The credentials manager will automatically refresh credentials
    when they are about to expire (< 5 minutes).

    If AssumeRole is disabled, CKAN will use static SMTP credentials
    from the config file (backward compatibility).

    :param config: CKAN config object
    :type config: dict
    """
    use_assume_role = tk.asbool(config.get('ckanext.hdx_smtp_assumerole.use_assume_role', False))

    if not use_assume_role:
        log.debug('SMTP AssumeRole is DISABLED. Using static SMTP credentials from config.')
        return

    log.debug('SMTP AssumeRole is ENABLED. Switching to SES API with auto-refresh...')

    try:
        # Validate required parameters
        role_name_or_arn = config.get('ckanext.hdx_smtp_assumerole.role_arn')
        region = config.get('ckanext.hdx_smtp_assumerole.region')

        if not role_name_or_arn:
            raise SMTPAssumeRoleException(
                'ckanext.hdx_smtp_assumerole.role_arn is required when use_assume_role is enabled'
            )

        if not region:
            raise SMTPAssumeRoleException(
                'ckanext.hdx_smtp_assumerole.region is required when use_assume_role is enabled'
            )

        # Validate formats
        _validate_role_arn(role_name_or_arn)
        _validate_region(region)

        # Warm up the credentials cache (loads initial credentials)
        get_ses_credentials()

        # Apply monkey patches to replace SMTP with SES API
        log.debug('Applying patches to replace SMTP with SES API')
        patch_mailer_functions()  # Patch ckan.lib.mailer
        patch_hdx_users_mailer()  # Patch ckanext.hdx_users.helpers.mailer

        # Set up email domain defaults if configured
        smtp_domain = config.get('ckanext.hdx_smtp_assumerole.smtp_domain', '')
        if smtp_domain:
            if not config.get('email_to'):
                config['email_to'] = f'ckan@{smtp_domain}'
            if not config.get('error_email_from'):
                config['error_email_from'] = f'ckan@{smtp_domain}'
            if not config.get('smtp.mail_from'):
                config['smtp.mail_from'] = f'hdx@{smtp_domain}'

        # Get credentials info for logging
        creds_info = get_credentials_info()

        # Single concise success message
        log.info(f'SES API with AssumeRole enabled: region={region}, role={role_name_or_arn}, expires={creds_info.get("expiration_time")}')

    except (SMTPAssumeRoleException, SESAssumeRoleException) as e:
        log.error(f'SES AssumeRole configuration failed: {str(e)}')
        log.error('Email functionality will NOT work with AssumeRole.')
        log.error('To use static SMTP credentials, set: ckanext.hdx_smtp_assumerole.use_assume_role = false')
        raise
    except Exception as e:
        log.error(f'Unexpected error during SES AssumeRole setup: {str(e)}')
        log.error('Email functionality will NOT work with AssumeRole.')
        log.error('To use static SMTP credentials, set: ckanext.hdx_smtp_assumerole.use_assume_role = false')
        raise


@tk.blanket.config_declarations
class HDXSMTPAssumeRolePlugin(plugins.SingletonPlugin):
    """
    CKAN plugin for AWS SES API with AssumeRole support and automatic credential refresh.

    This plugin allows CKAN to send emails via AWS SES API (not SMTP) using temporary
    credentials obtained through AWS STS AssumeRole. This solves the problem that
    SES SMTP doesn't support session tokens from temporary credentials.

    Features:
    - SES API instead of SMTP: Supports temporary credentials with session tokens
    - Automatic credential refresh: Credentials refresh when < 5 minutes to expiry
    - Per-container independent: Each container manages its own credentials
    - Thread-safe: Safe for multi-threaded WSGI servers
    - Lazy loading: Credentials only refresh when sending email
    - No restart needed: Credentials refresh automatically before expiry
    - Backward compatible: Disable use_assume_role to use static SMTP credentials

    Why SES API instead of SMTP?
    - SMTP only supports username/password authentication
    - Temporary credentials from AssumeRole include a session token
    - SES SMTP cannot use session tokens -> authentication fails
    - SES API supports full temporary credentials with session token

    Configuration example in .ini file:

        # Enable SES API with AssumeRole (disable for static SMTP)
        ckanext.hdx_smtp_assumerole.use_assume_role = true

        # Role name (will deduce account ID) or full ARN
        ckanext.hdx_smtp_assumerole.role_arn = my-ses-role
        # OR
        # ckanext.hdx_smtp_assumerole.role_arn = arn:aws:iam::123456789012:role/my-ses-role

        # AWS region for SES
        ckanext.hdx_smtp_assumerole.region = us-east-1

        # Optional: Session name (default: ckan-smtp-session)
        ckanext.hdx_smtp_assumerole.session_name = ckan-smtp-session

        # Optional: Email domain for default addresses
        ckanext.hdx_smtp_assumerole.smtp_domain = example.com

    Backward Compatibility:
    To use static SMTP credentials (old system), set use_assume_role = false
    or simply don't set it (defaults to false). The plugin will not patch
    email senders and CKAN will use standard SMTP with static credentials.
    """

    plugins.implements(plugins.IConfigurer, inherit=False)
    plugins.implements(plugins.IMiddleware, inherit=True)

    __startup_tasks_done = False

    def update_config(self, config: Dict[str, Any]) -> None:
        """
        Update CKAN config with plugin settings.

        :param config: CKAN config object
        :type config: dict
        """
        # No template directories needed for this plugin
        pass

    def make_middleware(self, app: Any, config: Dict[str, Any]) -> Any:
        """
        Called during application initialization.
        This is where we run the AssumeRole logic at startup.

        :param app: WSGI application
        :param config: CKAN config object
        :return: WSGI application
        """
        if not HDXSMTPAssumeRolePlugin.__startup_tasks_done:
            run_on_startup(config)
            HDXSMTPAssumeRolePlugin.__startup_tasks_done = True
        return app
