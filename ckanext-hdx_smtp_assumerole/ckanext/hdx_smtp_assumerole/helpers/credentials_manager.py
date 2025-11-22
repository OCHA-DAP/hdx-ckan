# encoding: utf-8

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role import (
    assume_role_for_smtp,
    SMTPAssumeRoleException
)

log = logging.getLogger(__name__)


class SMTPCredentialsManager:
    """
    Singleton credentials manager for SMTP AssumeRole.

    Manages temporary AWS SES SMTP credentials with automatic refresh.
    Each container/process has its own independent instance (no shared state).
    Thread-safe within the same container using local RLock.

    Features:
    - Lazy refresh: only refreshes when credentials are about to expire
    - Thread-safe: uses RLock for atomic operations within container
    - Independent: no coordination needed between containers
    - Automatic: transparent refresh before email sending
    """

    _instance = None
    _lock = threading.RLock()

    def __init__(self) -> None:
        """Initialize credentials manager with empty state."""
        self.credentials: Optional[Dict[str, Any]] = None
        self.expiration_time: Optional[datetime] = None
        self.config: Optional[Dict[str, Any]] = None
        self.role_name_or_arn: Optional[str] = None
        self.region: Optional[str] = None
        self.session_name: Optional[str] = None
        self._initialized: bool = False

    @classmethod
    def get_instance(cls) -> 'SMTPCredentialsManager':
        """
        Get or create singleton instance.
        Thread-safe singleton creation.

        :return: SMTPCredentialsManager instance
        :rtype: SMTPCredentialsManager
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def initialize(self, config: Dict[str, Any]) -> None:
        """
        Initialize manager with configuration and load initial credentials.
        Should be called once at application startup.

        :param config: CKAN config dict
        :type config: dict
        """
        with self._lock:
            if self._initialized:
                log.debug('SMTPCredentialsManager already initialized, skipping')
                return

            log.debug('Initializing SES credentials manager')

            self.config = config
            self.role_name_or_arn = config.get('ckanext.hdx_smtp_assumerole.role_arn')
            self.region = config.get('ckanext.hdx_smtp_assumerole.region')
            self.session_name = config.get('ckanext.hdx_smtp_assumerole.session_name', 'ckan-ses-session')

            # Load initial credentials
            self._load_credentials()
            self._initialized = True

            log.debug('SES credentials manager initialized successfully')

    def ensure_fresh_credentials(self) -> None:
        """
        Ensure credentials are fresh and valid.
        Refreshes credentials if they expire within 5 minutes.
        Thread-safe - uses lock to prevent concurrent refreshes.

        This is the main entry point called before sending emails.
        """
        if not self._initialized:
            log.warning('SMTPCredentialsManager not initialized, skipping credential check')
            return

        if self._needs_refresh():
            with self._lock:
                # Double-check after acquiring lock (another thread might have refreshed)
                if self._needs_refresh():
                    log.info('Credentials expiring soon, refreshing...')
                    self._load_credentials()

    def _needs_refresh(self) -> bool:
        """
        Check if credentials need to be refreshed.
        Returns True if credentials don't exist or expire within 5 minutes.
        Thread-safe - acquires lock internally for consistent reads.

        :return: True if refresh is needed
        :rtype: bool
        """
        with self._lock:
            if self.credentials is None or self.expiration_time is None:
                log.debug('Credentials not loaded, refresh needed')
                return True

            # Use UTC timezone explicitly to avoid None tzinfo issues
            now = datetime.now(timezone.utc)
            # Ensure expiration_time is timezone-aware
            expiration = self.expiration_time
            if expiration.tzinfo is None:
                expiration = expiration.replace(tzinfo=timezone.utc)

            time_until_expiry = expiration - now

            # Refresh if less than 5 minutes until expiry
            if time_until_expiry < timedelta(minutes=5):
                log.debug(f'Credentials expire in {time_until_expiry}, refresh needed')
                return True

            log.debug(f'Credentials still valid for {time_until_expiry}, no refresh needed')
            return False

    def _load_credentials(self) -> None:
        """
        Load fresh credentials via AssumeRole.
        Updates credentials cache for SES API usage.
        Should only be called within a lock.

        :raises SMTPAssumeRoleException: If credential loading fails
        """
        try:
            log.debug(f'Loading fresh SES credentials via AssumeRole for role: {self.role_name_or_arn}')

            # Assume role and get temporary credentials
            credentials = assume_role_for_smtp(
                role_name_or_arn=self.role_name_or_arn,
                region=self.region,
                session_name=self.session_name
            )

            # Update cache
            self.credentials = credentials
            self.expiration_time = credentials['expiration']

            # Update CKAN config (currently no-op for SES API)
            self._update_ckan_config(credentials)

            log.debug(f'Successfully loaded fresh SES credentials, expire at: {self.expiration_time}')

        except SMTPAssumeRoleException as e:
            log.error(f'Failed to load SES credentials: {str(e)}')
            raise
        except Exception as e:
            log.error(f'Unexpected error loading SES credentials: {str(e)}')
            raise SMTPAssumeRoleException(f'Unexpected error: {str(e)}')

    def _update_ckan_config(self, credentials: Dict[str, Any]) -> None:
        """
        Update CKAN configuration (placeholder for future use).

        Note: With SES API, we don't need to update SMTP config settings
        since emails are sent via boto3 API calls, not SMTP protocol.

        :param credentials: Credentials dict from assume_role_for_smtp
        :type credentials: dict
        """
        # No config updates needed for SES API
        # Credentials are passed directly to boto3.client('ses')
        pass

    def get_ses_credentials(self) -> Optional[Dict[str, Any]]:
        """
        Get credentials for SES API usage.

        :return: Dict with AWS credentials for boto3
        :rtype: dict
        """
        with self._lock:
            if not self._initialized or self.credentials is None:
                return None

            return {
                'access_key': self.credentials.get('access_key'),
                'secret_key': self.credentials.get('secret_key'),
                'session_token': self.credentials.get('session_token'),
                'region': self.region
            }

    def get_credentials_info(self) -> Dict[str, Any]:
        """
        Get information about current credentials (for debugging/monitoring).

        :return: Dict with credentials info
        :rtype: dict
        """
        with self._lock:
            if not self._initialized or self.credentials is None:
                return {
                    'initialized': self._initialized,
                    'has_credentials': False
                }

            # Use UTC timezone explicitly to avoid None tzinfo issues
            now = datetime.now(timezone.utc)
            # Ensure expiration_time is timezone-aware
            expiration = self.expiration_time
            if expiration.tzinfo is None:
                expiration = expiration.replace(tzinfo=timezone.utc)

            time_until_expiry = expiration - now

            # Mask access key for security (show first 4 and last 4 chars)
            access_key = self.credentials.get('access_key', 'N/A')
            if len(access_key) > 8:
                masked_access_key = access_key[:4] + '***' + access_key[-4:]
            else:
                masked_access_key = access_key

            return {
                'initialized': True,
                'has_credentials': True,
                'expiration_time': str(self.expiration_time),
                'time_until_expiry': str(time_until_expiry),
                'needs_refresh': self._needs_refresh(),
                'region': self.region,
                'access_key': masked_access_key
            }
