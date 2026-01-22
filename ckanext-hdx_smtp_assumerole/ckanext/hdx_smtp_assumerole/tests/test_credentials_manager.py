# encoding: utf-8

import pytest
import mock
from datetime import datetime, timedelta, timezone

from ckanext.hdx_smtp_assumerole.helpers.credentials_manager import SMTPCredentialsManager


class TestSMTPCredentialsManager:
    """Tests for SMTPCredentialsManager with dogpile Redis caching"""

    def setup_method(self):
        """Reset singleton before each test"""
        SMTPCredentialsManager._instance = None

    def test_singleton_pattern(self):
        """Test that manager follows singleton pattern"""
        manager1 = SMTPCredentialsManager.get_instance()
        manager2 = SMTPCredentialsManager.get_instance()

        assert manager1 is manager2

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_initialize_success(self, mock_cached_load):
        """Test successful initialization"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_cached_load.return_value = {
            'access_key': 'AKIATEST123',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        assert manager._initialized
        assert manager.role_name_or_arn == 'test-role'
        assert manager.region == 'us-east-1'
        assert manager.credentials is not None

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_initialize_idempotent(self, mock_cached_load):
        """Test that initialize can be called multiple times safely"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_cached_load.return_value = {
            'access_key': 'AKIATEST123',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)
        manager.initialize(config)  # Second call should be no-op

        # Should only call cached_load once (during first init)
        assert mock_cached_load.call_count == 1

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_get_ses_credentials(self, mock_cached_load):
        """Test getting SES credentials - uses dogpile cache directly"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_cached_load.return_value = {
            'access_key': 'AKIATEST123',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        # Reset call count after init
        mock_cached_load.reset_mock()

        result = manager.get_ses_credentials()

        # Should call cached_load (dogpile handles actual caching)
        assert mock_cached_load.call_count == 1
        assert result['access_key'] == 'AKIATEST123'
        assert result['secret_key'] == 'test-secret'
        assert result['session_token'] == 'test-token'
        assert result['region'] == 'us-east-1'

    def test_get_ses_credentials_not_initialized(self):
        """Test getting SES credentials when not initialized"""
        manager = SMTPCredentialsManager.get_instance()

        result = manager.get_ses_credentials()

        assert result is None

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_get_credentials_info(self, mock_cached_load):
        """Test getting credentials info for debugging"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_cached_load.return_value = {
            'access_key': 'AKIATEST123456789',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        result = manager.get_credentials_info()

        assert result['initialized']
        assert result['has_credentials']
        assert result['region'] == 'us-east-1'
        # Check that access key is masked (first 4 + *** + last 4)
        assert result['access_key'] == 'AKIA***6789'
        assert 'expiration_time' in result

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_custom_session_name(self, mock_cached_load):
        """Test using custom session name from config"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_cached_load.return_value = {
            'access_key': 'AKIATEST123',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1',
            'ckanext.hdx_smtp_assumerole.session_name': 'my-custom-session'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        assert manager.session_name == 'my-custom-session'

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_cached_load_failure_raises_exception(self, mock_cached_load):
        """Test that cache load failure raises appropriate exception"""
        from ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role import SMTPAssumeRoleException
        from ckanext.hdx_smtp_assumerole.helpers.caching import SESAssumeRoleException

        mock_cached_load.side_effect = SESAssumeRoleException('AssumeRole failed: Access Denied')

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()

        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            manager.initialize(config)

        assert 'Access Denied' in str(exc_info.value)

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_concurrent_access_thread_safety(self, mock_cached_load):
        """Test that concurrent credential access is thread-safe"""
        import threading

        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_cached_load.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        # Simulate concurrent access from multiple threads
        results = []
        errors = []

        def get_creds():
            try:
                creds = manager.get_ses_credentials()
                results.append(creds)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=get_creds) for _ in range(10)]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # All threads should succeed
        assert len(errors) == 0
        assert len(results) == 10

        # All should get same credentials
        for creds in results:
            assert creds['access_key'] == 'AKIATEST'

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_get_ses_credentials_returns_none_before_init(self, mock_cached_load):
        """Test that get_ses_credentials returns None before initialization"""
        manager = SMTPCredentialsManager.get_instance()
        # Clear any previous state
        manager.credentials = None
        manager.expiration_time = None

        creds = manager.get_ses_credentials()
        assert creds is None

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_get_credentials_info_before_init(self, mock_cached_load):
        """Test get_credentials_info returns proper state before initialization"""
        manager = SMTPCredentialsManager.get_instance()
        manager.credentials = None
        manager.expiration_time = None
        manager._initialized = False

        info = manager.get_credentials_info()

        assert not info['initialized']
        assert not info['has_credentials']
        # When not initialized, only these two fields are present
        assert len(info) == 2

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_short_access_key_not_masked(self, mock_cached_load):
        """Test that short access keys (< 8 chars) are not masked"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_cached_load.return_value = {
            'access_key': 'AKIA123',  # Only 7 chars
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        info = manager.get_credentials_info()
        # Short keys should not be masked
        assert info['access_key'] == 'AKIA123'

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_dogpile_cache_called_on_get_credentials(self, mock_cached_load):
        """Test that dogpile cached function is called when getting credentials"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_cached_load.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        # Reset mock after init
        mock_cached_load.reset_mock()

        # Call get_ses_credentials multiple times
        for _ in range(5):
            manager.get_ses_credentials()

        # With dogpile, the cached function is called each time
        # (dogpile handles the actual Redis caching internally)
        assert mock_cached_load.call_count == 5

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_get_ses_credentials_returns_none_on_cache_failure(self, mock_cached_load):
        """Test that get_ses_credentials returns None when cache fails"""
        from ckanext.hdx_smtp_assumerole.helpers.caching import SESAssumeRoleException

        # First call succeeds for init
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_cached_load.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        # Subsequent calls fail
        mock_cached_load.side_effect = SESAssumeRoleException('Redis connection failed')

        result = manager.get_ses_credentials()
        assert result is None

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.cached_load_ses_credentials')
    def test_timezone_aware_expiration_handling(self, mock_cached_load):
        """Test that timezone-naive expiration times are handled correctly"""
        # Return timezone-naive datetime (some AWS SDKs do this)
        expiration_naive = datetime.now() + timedelta(hours=1)

        mock_cached_load.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration_naive,  # No timezone
            'region': 'us-east-1'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        # Should not raise exception - code handles timezone conversion
        info = manager.get_credentials_info()
        assert info['has_credentials']
