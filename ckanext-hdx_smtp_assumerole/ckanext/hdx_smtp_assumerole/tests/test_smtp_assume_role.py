# encoding: utf-8

import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timezone

from ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role import (
    build_role_arn,
    get_account_id_from_sts,
    assume_role_for_smtp,
    create_sts_client_with_instance_profile,
    SMTPAssumeRoleException
)


class TestBuildRoleArn(unittest.TestCase):
    """Tests for build_role_arn function"""

    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.get_account_id_from_sts')
    def test_build_role_arn_from_name(self, mock_get_account):
        """Test building ARN from role name"""
        mock_get_account.return_value = '123456789012'

        result = build_role_arn('my-test-role')

        self.assertEqual(result, 'arn:aws:iam::123456789012:role/my-test-role')
        mock_get_account.assert_called_once()

    def test_build_role_arn_already_arn(self):
        """Test that existing ARN is returned unchanged"""
        arn = 'arn:aws:iam::123456789012:role/existing-role'

        result = build_role_arn(arn)

        self.assertEqual(result, arn)

    def test_build_role_arn_empty_raises(self):
        """Test that empty role name raises exception"""
        with self.assertRaises(SMTPAssumeRoleException):
            build_role_arn('')

    def test_build_role_arn_none_raises(self):
        """Test that None role name raises exception"""
        with self.assertRaises(SMTPAssumeRoleException):
            build_role_arn(None)


class TestGetAccountIdFromSts(unittest.TestCase):
    """Tests for get_account_id_from_sts function"""

    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.create_sts_client_with_instance_profile')
    def test_get_account_id_success(self, mock_create_client):
        """Test successful account ID retrieval"""
        mock_client = Mock()
        mock_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_create_client.return_value = mock_client

        result = get_account_id_from_sts()

        self.assertEqual(result, '123456789012')
        mock_client.get_caller_identity.assert_called_once()

    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.create_sts_client_with_instance_profile')
    def test_get_account_id_boto_error(self, mock_create_client):
        """Test handling of boto errors"""
        from botocore.exceptions import ClientError

        mock_client = Mock()
        mock_client.get_caller_identity.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            'GetCallerIdentity'
        )
        mock_create_client.return_value = mock_client

        with self.assertRaises(SMTPAssumeRoleException):
            get_account_id_from_sts()


class TestAssumeRoleForSmtp(unittest.TestCase):
    """Tests for assume_role_for_smtp function"""

    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.build_role_arn')
    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.create_sts_client_with_instance_profile')
    def test_assume_role_success(self, mock_create_client, mock_build_arn):
        """Test successful role assumption"""
        mock_build_arn.return_value = 'arn:aws:iam::123456789012:role/test-role'

        mock_client = Mock()
        expiration = datetime.now(timezone.utc)
        mock_client.assume_role.return_value = {
            'Credentials': {
                'AccessKeyId': 'AKIATEST123',
                'SecretAccessKey': 'test-secret-key',
                'SessionToken': 'test-session-token',
                'Expiration': expiration
            }
        }
        mock_create_client.return_value = mock_client

        result = assume_role_for_smtp('test-role', 'us-east-1')

        self.assertEqual(result['access_key'], 'AKIATEST123')
        self.assertEqual(result['secret_key'], 'test-secret-key')
        self.assertEqual(result['session_token'], 'test-session-token')
        self.assertEqual(result['expiration'], expiration)

        mock_client.assume_role.assert_called_once()
        call_args = mock_client.assume_role.call_args[1]
        self.assertEqual(call_args['RoleArn'], 'arn:aws:iam::123456789012:role/test-role')
        self.assertEqual(call_args['RoleSessionName'], 'ckan-ses-session')

    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.build_role_arn')
    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.create_sts_client_with_instance_profile')
    def test_assume_role_custom_session_name(self, mock_create_client, mock_build_arn):
        """Test role assumption with custom session name"""
        mock_build_arn.return_value = 'arn:aws:iam::123456789012:role/test-role'

        mock_client = Mock()
        expiration = datetime.now(timezone.utc)
        mock_client.assume_role.return_value = {
            'Credentials': {
                'AccessKeyId': 'AKIATEST123',
                'SecretAccessKey': 'test-secret-key',
                'SessionToken': 'test-session-token',
                'Expiration': expiration
            }
        }
        mock_create_client.return_value = mock_client

        result = assume_role_for_smtp('test-role', 'us-east-1', session_name='custom-session')

        call_args = mock_client.assume_role.call_args[1]
        self.assertEqual(call_args['RoleSessionName'], 'custom-session')

    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.build_role_arn')
    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.create_sts_client_with_instance_profile')
    def test_assume_role_boto_error(self, mock_create_client, mock_build_arn):
        """Test handling of boto errors during assume role"""
        from botocore.exceptions import ClientError

        mock_build_arn.return_value = 'arn:aws:iam::123456789012:role/test-role'

        mock_client = Mock()
        mock_client.assume_role.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Not authorized'}},
            'AssumeRole'
        )
        mock_create_client.return_value = mock_client

        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            assume_role_for_smtp('test-role', 'us-east-1')

        self.assertIn('Failed to assume role', str(ctx.exception))


class TestCreateStsClientWithInstanceProfile(unittest.TestCase):
    """Tests for create_sts_client_with_instance_profile function"""

    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.InstanceMetadataFetcher')
    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.InstanceMetadataProvider')
    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.boto3')
    def test_create_sts_client_success(self, mock_boto3, mock_provider_class, mock_fetcher_class):
        """Test successful STS client creation with instance profile"""
        # Mock credentials from instance metadata
        mock_creds = Mock()
        mock_creds.access_key = 'AKIAINSTANCE123'
        mock_creds.secret_key = 'instance-secret-key'
        mock_creds.token = 'instance-session-token'

        mock_provider = Mock()
        mock_provider.load.return_value = mock_creds
        mock_provider_class.return_value = mock_provider

        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        result = create_sts_client_with_instance_profile()

        self.assertEqual(result, mock_client)
        mock_boto3.client.assert_called_once_with(
            'sts',
            aws_access_key_id='AKIAINSTANCE123',
            aws_secret_access_key='instance-secret-key',
            aws_session_token='instance-session-token'
        )

    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.InstanceMetadataFetcher')
    @patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.InstanceMetadataProvider')
    def test_create_sts_client_no_instance_profile(self, mock_provider_class, mock_fetcher_class):
        """Test error when instance profile is not available"""
        mock_provider = Mock()
        mock_provider.load.side_effect = Exception('Unable to retrieve credentials')
        mock_provider_class.return_value = mock_provider

        with self.assertRaises(SMTPAssumeRoleException) as ctx:
            create_sts_client_with_instance_profile()

        self.assertIn('Failed to create STS client', str(ctx.exception))
