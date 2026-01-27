# encoding: utf-8

import pytest
import mock
from datetime import datetime, timedelta, timezone

from ckanext.hdx_smtp_assumerole.plugin import (
    run_on_startup,
    HDXSMTPAssumeRolePlugin,
    _validate_region,
    _validate_role_arn
)
from ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role import SMTPAssumeRoleException


class TestRunOnStartup:
    """Tests for run_on_startup function"""

    def test_disabled_exits_early(self):
        """Test that plugin exits early when use_assume_role is false"""
        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'false'
        }

        # Should not raise any exceptions, just return early
        run_on_startup(config)

    def test_disabled_default_exits_early(self):
        """Test that plugin exits early when use_assume_role is not set (defaults to false)"""
        config = {}

        # Should not raise any exceptions, just return early
        run_on_startup(config)

    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_ses_credentials')
    def test_enabled_missing_role_arn(self, mock_cached_load, mock_patch_mailer, mock_patch_hdx):
        """Test that missing role_arn raises exception"""
        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
            # Missing role_arn
        }

        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            run_on_startup(config)

        assert 'role_arn is required' in str(exc_info.value)

    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_ses_credentials')
    def test_enabled_missing_region(self, mock_cached_load, mock_patch_mailer, mock_patch_hdx):
        """Test that missing region raises exception"""
        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role'
            # Missing region
        }

        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            run_on_startup(config)

        assert 'region is required' in str(exc_info.value)

    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_credentials_info')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_ses_credentials')
    def test_enabled_success(self, mock_cached_load, mock_get_info, mock_patch_mailer, mock_patch_hdx):
        """Test successful plugin initialization when enabled"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_cached_load.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }
        mock_get_info.return_value = {
            'has_credentials': True,
            'expiration_time': str(expiration),
            'region': 'us-east-1',
            'access_key': 'AKIA***TEST'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        run_on_startup(config)

        # Verify cache was warmed up
        mock_cached_load.assert_called_once()

        # Verify both patchers were called
        mock_patch_mailer.assert_called_once()
        mock_patch_hdx.assert_called_once()

    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_credentials_info')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_ses_credentials')
    def test_enabled_with_smtp_domain(self, mock_cached_load, mock_get_info, mock_patch_mailer, mock_patch_hdx):
        """Test that smtp_domain configures email addresses"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_cached_load.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }
        mock_get_info.return_value = {
            'has_credentials': True,
            'expiration_time': str(expiration),
            'region': 'us-east-1',
            'access_key': 'AKIA***TEST'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1',
            'ckanext.hdx_smtp_assumerole.smtp_domain': 'example.com'
        }

        run_on_startup(config)

        # Verify email addresses were configured
        assert config['email_to'] == 'ckan@example.com'
        assert config['error_email_from'] == 'ckan@example.com'
        assert config['smtp.mail_from'] == 'hdx@example.com'

    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_credentials_info')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_ses_credentials')
    def test_enabled_smtp_domain_no_override(self, mock_cached_load, mock_get_info, mock_patch_mailer, mock_patch_hdx):
        """Test that smtp_domain doesn't override existing email addresses"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_cached_load.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }
        mock_get_info.return_value = {
            'has_credentials': True,
            'expiration_time': str(expiration),
            'region': 'us-east-1',
            'access_key': 'AKIA***TEST'
        }

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1',
            'ckanext.hdx_smtp_assumerole.smtp_domain': 'example.com',
            'email_to': 'existing@other.com',
            'smtp.mail_from': 'existing@other.com'
        }

        run_on_startup(config)

        # Verify existing values are not overridden
        assert config['email_to'] == 'existing@other.com'
        assert config['smtp.mail_from'] == 'existing@other.com'
        # But error_email_from should be set since it wasn't present
        assert config['error_email_from'] == 'ckan@example.com'


class TestHDXSMTPAssumeRolePlugin:
    """Tests for HDXSMTPAssumeRolePlugin class"""

    def test_plugin_implements_interfaces(self):
        """Test that plugin implements required interfaces"""
        import ckan.plugins as p

        plugin = HDXSMTPAssumeRolePlugin()

        # Check that plugin has the required methods from interfaces
        # IConfigurer requires update_config
        assert hasattr(plugin, 'update_config')
        assert callable(getattr(plugin, 'update_config'))

        # IMiddleware requires make_middleware
        assert hasattr(plugin, 'make_middleware')
        assert callable(getattr(plugin, 'make_middleware'))

        # Verify plugin class is registered
        assert isinstance(plugin, p.SingletonPlugin)

    def test_update_config(self):
        """Test update_config method"""
        plugin = HDXSMTPAssumeRolePlugin()
        config = {}

        # Should not raise any exceptions
        plugin.update_config(config)

    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.run_on_startup')
    def test_make_middleware_runs_once(self, mock_run_on_startup):
        """Test that make_middleware only runs startup tasks once"""
        HDXSMTPAssumeRolePlugin._HDXSMTPAssumeRolePlugin__startup_tasks_done = False

        plugin = HDXSMTPAssumeRolePlugin()
        app = mock.Mock()
        config = {'test': 'config'}

        # First call should run startup
        result1 = plugin.make_middleware(app, config)
        assert mock_run_on_startup.call_count == 1

        # Second call should not run startup again
        result2 = plugin.make_middleware(app, config)
        assert mock_run_on_startup.call_count == 1

        # Should return the app unchanged
        assert result1 == app
        assert result2 == app


class TestValidateRegion:
    """Tests for _validate_region function"""

    def test_valid_region_us_east_1(self):
        """Test valid region: us-east-1"""
        _validate_region('us-east-1')

    def test_valid_region_eu_west_2(self):
        """Test valid region: eu-west-2"""
        _validate_region('eu-west-2')

    def test_valid_region_ap_southeast_1(self):
        """Test valid region: ap-southeast-1"""
        _validate_region('ap-southeast-1')

    def test_valid_region_ca_central_1(self):
        """Test valid region: ca-central-1"""
        _validate_region('ca-central-1')

    def test_invalid_region_no_dashes(self):
        """Test invalid region: no dashes"""
        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            _validate_region('useast1')
        assert 'Invalid AWS region format' in str(exc_info.value)

    def test_invalid_region_uppercase(self):
        """Test invalid region: uppercase letters"""
        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            _validate_region('US-EAST-1')
        assert 'Invalid AWS region format' in str(exc_info.value)

    def test_invalid_region_empty(self):
        """Test invalid region: empty string"""
        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            _validate_region('')
        assert 'AWS region cannot be empty' in str(exc_info.value)


class TestValidateRoleArn:
    """Tests for _validate_role_arn function"""

    def test_valid_full_arn(self):
        """Test valid full ARN"""
        _validate_role_arn('arn:aws:iam::123456789012:role/MyRole')

    def test_valid_arn_with_path(self):
        """Test valid ARN with path"""
        _validate_role_arn('arn:aws:iam::123456789012:role/service-role/MyRole')

    def test_valid_role_name_simple(self):
        """Test valid simple role name"""
        _validate_role_arn('MyRole')

    def test_valid_role_name_with_dash(self):
        """Test valid role name with dash"""
        _validate_role_arn('My-Role')

    def test_invalid_arn_wrong_service(self):
        """Test invalid ARN: wrong service (not iam)"""
        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            _validate_role_arn('arn:aws:s3::123456789012:role/MyRole')
        assert 'Invalid IAM role ARN format' in str(exc_info.value)

    def test_invalid_role_name_with_slash(self):
        """Test invalid role name: contains slash (not full ARN)"""
        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            _validate_role_arn('My/Role')
        assert 'Invalid IAM role name' in str(exc_info.value)

    def test_invalid_role_name_empty(self):
        """Test invalid role name: empty string"""
        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            _validate_role_arn('')
        assert 'IAM role ARN or name cannot be empty' in str(exc_info.value)


class TestRunOnStartupValidation:
    """Tests for validation in run_on_startup function"""

    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_ses_credentials')
    def test_invalid_region_raises(self, mock_cached_load, mock_patch_mailer, mock_patch_hdx):
        """Test that invalid region format raises exception"""
        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'INVALID_REGION'
        }

        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            run_on_startup(config)

        assert 'Invalid AWS region format' in str(exc_info.value)

    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_ses_credentials')
    def test_invalid_role_arn_raises(self, mock_cached_load, mock_patch_mailer, mock_patch_hdx):
        """Test that invalid role ARN format raises exception"""
        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'invalid/role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            run_on_startup(config)

        assert 'Invalid IAM role name' in str(exc_info.value)

    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_credentials_info')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_ses_credentials')
    def test_valid_role_name_passes(self, mock_cached_load, mock_get_info, mock_patch_mailer, mock_patch_hdx):
        """Test that valid role name passes validation"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_cached_load.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }
        mock_get_info.return_value = {
            'has_credentials': True,
            'expiration_time': str(expiration)
        }

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'MyTestRole',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        run_on_startup(config)
        mock_cached_load.assert_called_once()


class TestRunOnStartupEdgeCases:
    """Additional edge case tests for run_on_startup"""

    def test_disabled_with_various_false_values(self):
        """Test that various false values disable the plugin"""
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO']

        for val in false_values:
            config = {
                'ckanext.hdx_smtp_assumerole.use_assume_role': val
            }
            run_on_startup(config)

    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_credentials_info')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_ses_credentials')
    def test_enabled_with_empty_smtp_domain(self, mock_cached_load, mock_get_info, mock_patch_mailer, mock_patch_hdx):
        """Test with empty smtp_domain config"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_cached_load.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'expiration': expiration,
            'region': 'us-east-1'
        }
        mock_get_info.return_value = {
            'has_credentials': True,
            'expiration_time': str(expiration)
        }

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1',
            'ckanext.hdx_smtp_assumerole.smtp_domain': ''
        }

        run_on_startup(config)

        # Should not set email addresses when smtp_domain is empty
        assert 'email_to' not in config

    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @mock.patch('ckanext.hdx_smtp_assumerole.plugin.get_ses_credentials')
    def test_generic_exception_during_startup(self, mock_cached_load, mock_patch_mailer, mock_patch_hdx):
        """Test handling of unexpected exceptions during startup"""
        mock_cached_load.side_effect = Exception('Unexpected error')

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        with pytest.raises(Exception) as exc_info:
            run_on_startup(config)

        assert str(exc_info.value) == 'Unexpected error'
