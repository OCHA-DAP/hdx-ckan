# encoding: utf-8

import unittest
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from ckanext.hdx_smtp_assumerole.helpers.credentials_manager import SMTPCredentialsManager


class TestSMTPCredentialsManager(unittest.TestCase):
    """Tests for SMTPCredentialsManager"""

    def setUp(self):
        """Reset singleton before each test"""
        SMTPCredentialsManager._instance = None

    def test_singleton_pattern(self):
        """Test that manager follows singleton pattern"""
        manager1 = SMTPCredentialsManager.get_instance()
        manager2 = SMTPCredentialsManager.get_instance()

        self.assertIs(manager1, manager2)

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_initialize_success(self, mock_assume_role):
        """Test successful initialization"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_assume_role.return_value = {
            'access_key': 'AKIATEST123',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        self.assertTrue(manager._initialized)
        self.assertEqual(manager.role_name_or_arn, 'test-role')
        self.assertEqual(manager.region, 'us-east-1')
        self.assertIsNotNone(manager.credentials)

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_initialize_idempotent(self, mock_assume_role):
        """Test that initialize can be called multiple times safely"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_assume_role.return_value = {
            'access_key': 'AKIATEST123',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)
        manager.initialize(config)  # Second call should be no-op

        # Should only call assume_role once
        self.assertEqual(mock_assume_role.call_count, 1)

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_needs_refresh_not_initialized(self, mock_assume_role):
        """Test needs_refresh when not initialized"""
        manager = SMTPCredentialsManager.get_instance()

        result = manager._needs_refresh()

        self.assertTrue(result)

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_needs_refresh_expiring_soon(self, mock_assume_role):
        """Test needs_refresh when credentials expire in < 5 minutes"""
        # Credentials expire in 3 minutes
        expiration = datetime.now(timezone.utc) + timedelta(minutes=3)
        mock_assume_role.return_value = {
            'access_key': 'AKIATEST123',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        result = manager._needs_refresh()

        self.assertTrue(result)

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_needs_refresh_not_expiring(self, mock_assume_role):
        """Test needs_refresh when credentials are still valid"""
        # Credentials expire in 30 minutes
        expiration = datetime.now(timezone.utc) + timedelta(minutes=30)
        mock_assume_role.return_value = {
            'access_key': 'AKIATEST123',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        result = manager._needs_refresh()

        self.assertFalse(result)

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_ensure_fresh_credentials_triggers_refresh(self, mock_assume_role):
        """Test that ensure_fresh_credentials triggers refresh when needed"""
        # First call - credentials expire in 30 minutes
        expiration1 = datetime.now(timezone.utc) + timedelta(minutes=30)
        # Second call (refresh) - credentials expire in 1 hour
        expiration2 = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_assume_role.side_effect = [
            {
                'access_key': 'AKIATEST123',
                'secret_key': 'test-secret',
                'session_token': 'test-token',
                'expiration': expiration1
            },
            {
                'access_key': 'AKIATEST456',
                'secret_key': 'test-secret-new',
                'session_token': 'test-token-new',
                'expiration': expiration2
            }
        ]

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        # Force expiration to be soon
        manager.expiration_time = datetime.now(timezone.utc) + timedelta(minutes=3)

        manager.ensure_fresh_credentials()

        # Should have called assume_role twice (initial + refresh)
        self.assertEqual(mock_assume_role.call_count, 2)
        self.assertEqual(manager.credentials['access_key'], 'AKIATEST456')

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_get_ses_credentials(self, mock_assume_role):
        """Test getting SES credentials for API usage"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_assume_role.return_value = {
            'access_key': 'AKIATEST123',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        result = manager.get_ses_credentials()

        self.assertEqual(result['access_key'], 'AKIATEST123')
        self.assertEqual(result['secret_key'], 'test-secret')
        self.assertEqual(result['session_token'], 'test-token')
        self.assertEqual(result['region'], 'us-east-1')

    def test_get_ses_credentials_not_initialized(self):
        """Test getting SES credentials when not initialized"""
        manager = SMTPCredentialsManager.get_instance()

        result = manager.get_ses_credentials()

        self.assertIsNone(result)

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_get_credentials_info(self, mock_assume_role):
        """Test getting credentials info for debugging"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_assume_role.return_value = {
            'access_key': 'AKIATEST123456789',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        result = manager.get_credentials_info()

        self.assertTrue(result['initialized'])
        self.assertTrue(result['has_credentials'])
        self.assertEqual(result['region'], 'us-east-1')
        # Check that access key is masked (first 4 + *** + last 4)
        self.assertEqual(result['access_key'], 'AKIA***6789')
        self.assertIn('expiration_time', result)

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_custom_session_name(self, mock_assume_role):
        """Test using custom session name"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_assume_role.return_value = {
            'access_key': 'AKIATEST123',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1',
            'ckanext.hdx_smtp_assumerole.session_name': 'my-custom-session'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        self.assertEqual(manager.session_name, 'my-custom-session')
        mock_assume_role.assert_called_with(
            role_name_or_arn='test-role',
            region='us-east-1',
            session_name='my-custom-session'
        )

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_expired_credentials_refresh(self, mock_assume_role):
        """Test that expired credentials are automatically refreshed"""
        # First call - credentials already expired
        expiration1 = datetime.now(timezone.utc) - timedelta(minutes=10)
        # Second call - fresh credentials
        expiration2 = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_assume_role.side_effect = [
            {
                'access_key': 'AKIAOLD',
                'secret_key': 'old-secret',
                'session_token': 'old-token',
                'expiration': expiration1
            },
            {
                'access_key': 'AKIANEW',
                'secret_key': 'new-secret',
                'session_token': 'new-token',
                'expiration': expiration2
            }
        ]

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        # First call loads expired credentials
        self.assertEqual(mock_assume_role.call_count, 1)

        # Call ensure_fresh_credentials - should trigger refresh because expired
        manager.ensure_fresh_credentials()

        # Should have called assume_role again to refresh
        self.assertEqual(mock_assume_role.call_count, 2)

        # Now get the refreshed credentials
        creds = manager.get_ses_credentials()
        self.assertEqual(creds['access_key'], 'AKIANEW')

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_assume_role_failure_raises_exception(self, mock_assume_role):
        """Test that AssumeRole failure raises appropriate exception"""
        from ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role import SMTPAssumeRoleException

        mock_assume_role.side_effect = SMTPAssumeRoleException('AssumeRole failed: Access Denied')

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()

        with self.assertRaises(SMTPAssumeRoleException) as context:
            manager.initialize(config)

        self.assertIn('Access Denied', str(context.exception))

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_concurrent_refresh_thread_safety(self, mock_assume_role):
        """Test that concurrent credential refreshes are thread-safe"""
        import threading

        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_assume_role.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        # Force expiration
        manager.expiration_time = datetime.now(timezone.utc) + timedelta(minutes=3)

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
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(results), 10)

        # All should get same credentials
        for creds in results:
            self.assertEqual(creds['access_key'], 'AKIATEST')

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_get_ses_credentials_returns_none_before_init(self, mock_assume_role):
        """Test that get_ses_credentials returns None before initialization"""
        manager = SMTPCredentialsManager.get_instance()
        # Clear any previous state
        manager.credentials = None
        manager.expiration_time = None

        creds = manager.get_ses_credentials()
        self.assertIsNone(creds)

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_get_credentials_info_before_init(self, mock_assume_role):
        """Test get_credentials_info returns proper state before initialization"""
        manager = SMTPCredentialsManager.get_instance()
        manager.credentials = None
        manager.expiration_time = None
        manager._initialized = False

        info = manager.get_credentials_info()

        self.assertFalse(info['initialized'])
        self.assertFalse(info['has_credentials'])
        # When not initialized, only these two fields are present
        self.assertEqual(len(info), 2)

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_short_access_key_not_masked(self, mock_assume_role):
        """Test that short access keys (< 8 chars) are not masked"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)
        mock_assume_role.return_value = {
            'access_key': 'AKIA123',  # Only 7 chars
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        info = manager.get_credentials_info()
        # Short keys should not be masked
        self.assertEqual(info['access_key'], 'AKIA123')

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_multiple_refresh_cycles(self, mock_assume_role):
        """Test multiple refresh cycles work correctly"""
        expirations = [
            datetime.now(timezone.utc) + timedelta(hours=1),
            datetime.now(timezone.utc) + timedelta(hours=2),
            datetime.now(timezone.utc) + timedelta(hours=3),
        ]

        mock_assume_role.side_effect = [
            {
                'access_key': f'AKIA{i}',
                'secret_key': f'secret-{i}',
                'session_token': f'token-{i}',
                'expiration': exp
            }
            for i, exp in enumerate(expirations)
        ]

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        # Force refresh twice
        for i in range(2):
            manager.expiration_time = datetime.now(timezone.utc) + timedelta(minutes=3)
            manager.ensure_fresh_credentials()

        # Should have called assume_role 3 times (init + 2 refreshes)
        self.assertEqual(mock_assume_role.call_count, 3)

    @patch('ckanext.hdx_smtp_assumerole.helpers.credentials_manager.assume_role_for_smtp')
    def test_timezone_aware_expiration_handling(self, mock_assume_role):
        """Test that timezone-naive expiration times are handled correctly"""
        # Return timezone-naive datetime (some AWS SDKs do this)
        expiration_naive = datetime.now() + timedelta(hours=1)

        mock_assume_role.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration_naive  # No timezone
        }

        config = {
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        manager = SMTPCredentialsManager.get_instance()
        manager.initialize(config)

        # Should not raise exception - code handles timezone conversion
        info = manager.get_credentials_info()
        self.assertTrue(info['has_credentials'])
