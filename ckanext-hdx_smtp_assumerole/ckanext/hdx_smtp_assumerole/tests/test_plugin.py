# encoding: utf-8

import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta, timezone

from ckanext.hdx_smtp_assumerole.plugin import (
    run_on_startup,
    HDXSMTPAssumeRolePlugin,
    _validate_region,
    _validate_role_arn
)
from ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role import SMTPAssumeRoleException


class TestRunOnStartup(unittest.TestCase):
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

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_enabled_missing_role_arn(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test that missing role_arn raises exception"""
        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
            # Missing role_arn
        }

        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            run_on_startup(config)

        self.assertIn('role_arn is required', str(ctx.exception))

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_enabled_missing_region(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test that missing region raises exception"""
        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role'
            # Missing region
        }

        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            run_on_startup(config)

        self.assertIn('region is required', str(ctx.exception))

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_enabled_success(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test successful plugin initialization when enabled"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_manager = Mock()
        mock_manager.get_credentials_info.return_value = {
            'initialized': True,
            'has_credentials': True,
            'expiration_time': str(expiration),
            'region': 'us-east-1',
            'access_key': 'AKIA***123'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        run_on_startup(config)

        # Verify manager was initialized
        mock_manager.initialize.assert_called_once_with(config)

        # Verify both patchers were called
        mock_patch_mailer.assert_called_once()
        mock_patch_hdx.assert_called_once()

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_enabled_with_smtp_domain(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test that smtp_domain configures email addresses"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_manager = Mock()
        mock_manager.get_credentials_info.return_value = {
            'initialized': True,
            'has_credentials': True,
            'expiration_time': str(expiration),
            'region': 'us-east-1',
            'access_key': 'AKIA***123'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1',
            'ckanext.hdx_smtp_assumerole.smtp_domain': 'example.com'
        }

        run_on_startup(config)

        # Verify email addresses were configured
        self.assertEqual(config['email_to'], 'ckan@example.com')
        self.assertEqual(config['error_email_from'], 'ckan@example.com')
        self.assertEqual(config['smtp.mail_from'], 'hdx@example.com')

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_enabled_smtp_domain_no_override(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test that smtp_domain doesn't override existing email addresses"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_manager = Mock()
        mock_manager.get_credentials_info.return_value = {
            'initialized': True,
            'has_credentials': True,
            'expiration_time': str(expiration),
            'region': 'us-east-1',
            'access_key': 'AKIA***123'
        }
        mock_manager_class.get_instance.return_value = mock_manager

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
        self.assertEqual(config['email_to'], 'existing@other.com')
        self.assertEqual(config['smtp.mail_from'], 'existing@other.com')
        # But error_email_from should be set since it wasn't present
        self.assertEqual(config['error_email_from'], 'ckan@example.com')


class TestHDXSMTPAssumeRolePlugin(unittest.TestCase):
    """Tests for HDXSMTPAssumeRolePlugin class"""

    def test_plugin_implements_interfaces(self):
        """Test that plugin implements required interfaces"""
        import ckan.plugins as p

        plugin = HDXSMTPAssumeRolePlugin()

        # Check that plugin has the required methods from interfaces
        # IConfigurer requires update_config
        self.assertTrue(hasattr(plugin, 'update_config'))
        self.assertTrue(callable(getattr(plugin, 'update_config')))

        # IMiddleware requires make_middleware
        self.assertTrue(hasattr(plugin, 'make_middleware'))
        self.assertTrue(callable(getattr(plugin, 'make_middleware')))

        # Verify plugin class is registered
        self.assertIsInstance(plugin, p.SingletonPlugin)

    def test_update_config(self):
        """Test update_config method"""
        plugin = HDXSMTPAssumeRolePlugin()
        config = {}

        # Should not raise any exceptions
        plugin.update_config(config)

    @patch('ckanext.hdx_smtp_assumerole.plugin.run_on_startup')
    def test_make_middleware_runs_once(self, mock_run_on_startup):
        """Test that make_middleware only runs startup tasks once"""
        HDXSMTPAssumeRolePlugin._HDXSMTPAssumeRolePlugin__startup_tasks_done = False

        plugin = HDXSMTPAssumeRolePlugin()
        app = Mock()
        config = {'test': 'config'}

        # First call should run startup
        result1 = plugin.make_middleware(app, config)
        self.assertEqual(mock_run_on_startup.call_count, 1)

        # Second call should not run startup again
        result2 = plugin.make_middleware(app, config)
        self.assertEqual(mock_run_on_startup.call_count, 1)

        # Should return the app unchanged
        self.assertEqual(result1, app)
        self.assertEqual(result2, app)


class TestValidateRegion(unittest.TestCase):
    """Tests for _validate_region function"""

    def test_valid_region_us_east_1(self):
        """Test valid region: us-east-1"""
        # Should not raise exception
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
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_region('useast1')
        self.assertIn('Invalid AWS region format', str(ctx.exception))
        self.assertIn('us-east-1', str(ctx.exception))

    def test_invalid_region_uppercase(self):
        """Test invalid region: uppercase letters"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_region('US-EAST-1')
        self.assertIn('Invalid AWS region format', str(ctx.exception))

    def test_invalid_region_too_many_parts(self):
        """Test invalid region: too many parts"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_region('us-east-1-extra')
        self.assertIn('Invalid AWS region format', str(ctx.exception))

    def test_invalid_region_empty(self):
        """Test invalid region: empty string"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_region('')
        self.assertIn('Invalid AWS region format', str(ctx.exception))

    def test_invalid_region_special_chars(self):
        """Test invalid region: special characters"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_region('us_east_1')
        self.assertIn('Invalid AWS region format', str(ctx.exception))

    def test_invalid_region_no_number(self):
        """Test invalid region: missing number"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_region('us-east-')
        self.assertIn('Invalid AWS region format', str(ctx.exception))


class TestValidateRoleArn(unittest.TestCase):
    """Tests for _validate_role_arn function"""

    # Full ARN format tests
    def test_valid_full_arn(self):
        """Test valid full ARN"""
        # Should not raise exception
        _validate_role_arn('arn:aws:iam::123456789012:role/MyRole')

    def test_valid_arn_with_path(self):
        """Test valid ARN with path"""
        _validate_role_arn('arn:aws:iam::123456789012:role/service-role/MyRole')

    def test_valid_arn_with_special_chars(self):
        """Test valid ARN with special characters in role name"""
        _validate_role_arn('arn:aws:iam::123456789012:role/My-Role_123+test')

    def test_invalid_arn_wrong_service(self):
        """Test invalid ARN: wrong service (not iam)"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_role_arn('arn:aws:s3::123456789012:role/MyRole')
        self.assertIn('Invalid IAM role ARN format', str(ctx.exception))
        self.assertIn('arn:aws:iam::ACCOUNT_ID:role/ROLE_NAME', str(ctx.exception))

    def test_invalid_arn_missing_account_id(self):
        """Test invalid ARN: missing account ID"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_role_arn('arn:aws:iam:::role/MyRole')
        self.assertIn('Invalid IAM role ARN format', str(ctx.exception))

    def test_invalid_arn_short_account_id(self):
        """Test invalid ARN: account ID too short"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_role_arn('arn:aws:iam::12345:role/MyRole')
        self.assertIn('Invalid IAM role ARN format', str(ctx.exception))

    def test_invalid_arn_no_role_name(self):
        """Test invalid ARN: no role name after role/"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_role_arn('arn:aws:iam::123456789012:role/')
        self.assertIn('Invalid IAM role ARN format', str(ctx.exception))

    def test_invalid_arn_wrong_resource_type(self):
        """Test invalid ARN: wrong resource type (not role)"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_role_arn('arn:aws:iam::123456789012:user/MyUser')
        self.assertIn('Invalid IAM role ARN format', str(ctx.exception))

    # Role name format tests
    def test_valid_role_name_simple(self):
        """Test valid simple role name"""
        _validate_role_arn('MyRole')

    def test_valid_role_name_with_dash(self):
        """Test valid role name with dash"""
        _validate_role_arn('My-Role')

    def test_valid_role_name_with_underscore(self):
        """Test valid role name with underscore"""
        _validate_role_arn('My_Role')

    def test_valid_role_name_with_plus(self):
        """Test valid role name with plus"""
        _validate_role_arn('My+Role')

    def test_valid_role_name_with_equals(self):
        """Test valid role name with equals"""
        _validate_role_arn('My=Role')

    def test_valid_role_name_with_comma(self):
        """Test valid role name with comma"""
        _validate_role_arn('My,Role')

    def test_valid_role_name_with_period(self):
        """Test valid role name with period"""
        _validate_role_arn('My.Role')

    def test_valid_role_name_with_at(self):
        """Test valid role name with @"""
        _validate_role_arn('My@Role')

    def test_invalid_role_name_with_slash(self):
        """Test invalid role name: contains slash (not full ARN)"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_role_arn('My/Role')
        self.assertIn('Invalid IAM role name', str(ctx.exception))
        self.assertIn('+ = , . @ -', str(ctx.exception))

    def test_invalid_role_name_with_space(self):
        """Test invalid role name: contains space"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_role_arn('My Role')
        self.assertIn('Invalid IAM role name', str(ctx.exception))

    def test_invalid_role_name_with_special_char(self):
        """Test invalid role name: contains invalid special character"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_role_arn('My#Role')
        self.assertIn('Invalid IAM role name', str(ctx.exception))

    def test_invalid_role_name_empty(self):
        """Test invalid role name: empty string"""
        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            _validate_role_arn('')
        self.assertIn('Invalid IAM role name', str(ctx.exception))


class TestRunOnStartupValidation(unittest.TestCase):
    """Tests for validation in run_on_startup function"""

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_invalid_region_raises(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test that invalid region format raises exception"""
        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'INVALID_REGION'
        }

        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            run_on_startup(config)

        self.assertIn('Invalid AWS region format', str(ctx.exception))

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_invalid_role_arn_raises(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test that invalid role ARN format raises exception"""
        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'invalid/role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            run_on_startup(config)

        self.assertIn('Invalid IAM role name', str(ctx.exception))

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_valid_role_name_passes(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test that valid role name passes validation"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_manager = Mock()
        mock_manager.get_credentials_info.return_value = {
            'initialized': True,
            'has_credentials': True,
            'expiration_time': str(expiration),
            'region': 'us-east-1',
            'access_key': 'AKIA***123'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'MyTestRole',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        # Should not raise exception
        run_on_startup(config)

        mock_manager.initialize.assert_called_once_with(config)

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_valid_full_arn_passes(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test that valid full ARN passes validation"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_manager = Mock()
        mock_manager.get_credentials_info.return_value = {
            'initialized': True,
            'has_credentials': True,
            'expiration_time': str(expiration),
            'region': 'us-east-1',
            'access_key': 'AKIA***123'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'arn:aws:iam::123456789012:role/MyTestRole',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        # Should not raise exception
        run_on_startup(config)

        mock_manager.initialize.assert_called_once_with(config)


class TestValidateRegionEdgeCases(unittest.TestCase):
    """Additional edge case tests for region validation"""

    def test_region_with_numbers_only(self):
        """Test region with multiple numbers"""
        _validate_region('us-east-12')

    def test_region_different_patterns(self):
        """Test various valid region patterns"""
        valid_regions = [
            'us-east-1',
            'us-west-2',
            'eu-west-1',
            'eu-central-1',
            'ap-south-1',
            'ap-northeast-1',
            'ap-northeast-2',
            'ap-southeast-1',
            'ap-southeast-2',
            'ca-central-1',
            'sa-east-1',
            'me-south-1',
            'af-south-1',
        ]
        for region in valid_regions:
            _validate_region(region)

    def test_invalid_region_three_letter_prefix(self):
        """Test invalid region with 3-letter prefix"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_region('usa-east-1')

    def test_invalid_region_single_letter_direction(self):
        """Test invalid region with single letter direction"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_region('us-e-1')

    def test_invalid_region_no_region_part(self):
        """Test invalid region missing region part"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_region('us-1')

    def test_invalid_region_trailing_dash(self):
        """Test invalid region with trailing dash"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_region('us-east-1-')

    def test_invalid_region_leading_dash(self):
        """Test invalid region with leading dash"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_region('-us-east-1')

    def test_invalid_region_multiple_dashes(self):
        """Test invalid region with multiple consecutive dashes"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_region('us--east-1')


class TestValidateRoleArnEdgeCases(unittest.TestCase):
    """Additional edge case tests for role ARN validation"""

    def test_role_arn_max_length_path(self):
        """Test ARN with very deep path"""
        _validate_role_arn('arn:aws:iam::123456789012:role/path/to/very/deep/nested/role/MyRole')

    def test_role_arn_with_numbers_in_path(self):
        """Test ARN with numbers in path"""
        _validate_role_arn('arn:aws:iam::123456789012:role/service-123/role-456')

    def test_role_name_with_all_special_chars(self):
        """Test role name with all allowed special characters"""
        _validate_role_arn('My+Role=Test.Name@Domain,Version-1')

    def test_role_name_starting_with_number(self):
        """Test role name starting with number"""
        _validate_role_arn('123MyRole')

    def test_role_name_all_numbers(self):
        """Test role name with only numbers"""
        _validate_role_arn('123456789')

    def test_invalid_arn_wrong_partition(self):
        """Test invalid ARN with wrong partition"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_role_arn('arn:aws-cn:iam::123456789012:role/MyRole')

    def test_invalid_arn_missing_colon(self):
        """Test invalid ARN with missing colon separator"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_role_arn('arnawsiam::123456789012:role/MyRole')

    def test_invalid_arn_extra_colon(self):
        """Test invalid ARN with extra colon"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_role_arn('arn:aws:iam:::123456789012:role/MyRole')

    def test_invalid_arn_letters_in_account_id(self):
        """Test invalid ARN with letters in account ID"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_role_arn('arn:aws:iam::12345ABC9012:role/MyRole')

    def test_invalid_arn_13_digit_account_id(self):
        """Test invalid ARN with 13-digit account ID"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_role_arn('arn:aws:iam::1234567890123:role/MyRole')

    def test_invalid_role_name_with_asterisk(self):
        """Test invalid role name with asterisk"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_role_arn('My*Role')

    def test_invalid_role_name_with_dollar(self):
        """Test invalid role name with dollar sign"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_role_arn('My$Role')

    def test_invalid_role_name_with_percent(self):
        """Test invalid role name with percent sign"""
        with self.assertRaises(SMTPAssumeRoleException):
            _validate_role_arn('My%Role')


class TestRunOnStartupEdgeCases(unittest.TestCase):
    """Additional edge case tests for run_on_startup"""

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_enabled_with_whitespace_in_config(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test that whitespace in config values is handled"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_manager = Mock()
        mock_manager.get_credentials_info.return_value = {
            'initialized': True,
            'has_credentials': True,
            'expiration_time': str(expiration),
            'region': 'us-east-1',
            'access_key': 'AKIA***123'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': '  test-role  ',  # Whitespace
            'ckanext.hdx_smtp_assumerole.region': ' us-east-1 '  # Whitespace
        }

        # Should handle whitespace - validation will fail on ' us-east-1 '
        with self.assertRaises(SMTPAssumeRoleException):
            run_on_startup(config)

    def test_disabled_with_various_false_values(self):
        """Test that various false values disable the plugin"""
        false_values = ['false', 'False', 'FALSE', '0', 'no', 'No', 'NO']

        for val in false_values:
            config = {
                'ckanext.hdx_smtp_assumerole.use_assume_role': val
            }
            # Should not raise exception
            run_on_startup(config)

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_enabled_with_empty_smtp_domain(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test with empty smtp_domain config"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_manager = Mock()
        mock_manager.get_credentials_info.return_value = {
            'initialized': True,
            'has_credentials': True,
            'expiration_time': str(expiration),
            'region': 'us-east-1',
            'access_key': 'AKIA***123'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'test-role',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1',
            'ckanext.hdx_smtp_assumerole.smtp_domain': ''  # Empty
        }

        run_on_startup(config)

        # Should not set email addresses when smtp_domain is empty
        self.assertNotIn('email_to', config)

    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_hdx_users_mailer')
    @patch('ckanext.hdx_smtp_assumerole.plugin.patch_mailer_functions')
    @patch('ckanext.hdx_smtp_assumerole.plugin.SMTPCredentialsManager')
    def test_enabled_role_arn_case_sensitivity(self, mock_manager_class, mock_patch_mailer, mock_patch_hdx):
        """Test that role ARN validation is case-sensitive where needed"""
        expiration = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_manager = Mock()
        mock_manager.get_credentials_info.return_value = {
            'initialized': True,
            'has_credentials': True,
            'expiration_time': str(expiration),
            'region': 'us-east-1',
            'access_key': 'AKIA***123'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        # ARN with uppercase ARN: should fail
        config = {
            'ckanext.hdx_smtp_assumerole.use_assume_role': 'true',
            'ckanext.hdx_smtp_assumerole.role_arn': 'ARN:aws:iam::123456789012:role/MyRole',
            'ckanext.hdx_smtp_assumerole.region': 'us-east-1'
        }

        with self.assertRaises(SMTPAssumeRoleException):
            run_on_startup(config)
