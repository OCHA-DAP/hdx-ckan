# encoding: utf-8

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional

from ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role import SMTPAssumeRoleException
from ckanext.hdx_smtp_assumerole.helpers.caching import (
    cached_load_ses_credentials,
    SESAssumeRoleException
)

log = logging.getLogger(__name__)


class SMTPCredentialsManager:
    """
    Singleton credentials manager for SES AssumeRole.

    Wraps dogpile Redis-cached credentials for SES API usage.
    Credentials are cached in Redis with 55-minute TTL (5 min before expiry).
    All processes share the same Redis cache - no per-process state needed.

    Features:
    - Redis caching via dogpile (shared across all nginx unit processes)
    - Automatic refresh handled by dogpile TTL
    - Thread-safe singleton pattern for local state
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

    def _load_credentials(self) -> None:
        """
        Load credentials via dogpile-cached AssumeRole.
        Dogpile handles caching in Redis with 55-minute TTL.
        Should only be called within a lock.

        :raises SMTPAssumeRoleException: If credential loading fails
        """
        try:
            log.debug('Loading SES credentials via Redis-cached AssumeRole')

            # Load credentials from cache (Redis) or create new ones if cache expired
            # Dogpile automatically handles cache TTL and regeneration
            credentials = cached_load_ses_credentials()

            # Update local cache (for get_credentials_info)
            self.credentials = credentials
            self.expiration_time = credentials['expiration']

            # Mask access_key for logging - show only first 2 and last 2 chars
            access_key = credentials.get('access_key', 'None')
            if access_key != 'None' and len(access_key) > 4:
                masked_key = '{0}..{1}'.format(access_key[:2], access_key[-2:])
            else:
                masked_key = access_key
            log.info('Using SES credentials - access_key: {0}, expiration: {1}'.format(
                masked_key,
                credentials.get('expiration', 'None')
            ))

        except SESAssumeRoleException as e:
            log.error(f'Failed to load SES credentials: {str(e)}')
            raise SMTPAssumeRoleException(str(e))
        except Exception as e:
            log.error(f'Unexpected error loading SES credentials: {str(e)}')
            raise SMTPAssumeRoleException(f'Unexpected error: {str(e)}')

    def get_ses_credentials(self) -> Optional[Dict[str, Any]]:
        """
        Get credentials for SES API usage.
        Uses dogpile-cached credentials from Redis.

        :return: Dict with AWS credentials for boto3
        :rtype: dict
        """
        if not self._initialized:
            return None

        try:
            # Load credentials from cache (Redis) or create new ones if cache expired
            # Dogpile automatically handles cache TTL and regeneration
            credentials = cached_load_ses_credentials()

            return {
                'access_key': credentials.get('access_key'),
                'secret_key': credentials.get('secret_key'),
                'session_token': credentials.get('session_token'),
                'region': credentials.get('region')
            }
        except SESAssumeRoleException as e:
            log.error(f'Failed to get SES credentials: {str(e)}')
            return None

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
                'region': self.region,
                'access_key': masked_access_key
            }
