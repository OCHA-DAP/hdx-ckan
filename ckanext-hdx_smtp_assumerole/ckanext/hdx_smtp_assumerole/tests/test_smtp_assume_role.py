# encoding: utf-8

import pytest
import mock
from datetime import datetime, timezone

from ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role import (
    build_role_arn,
    get_account_id_from_sts,
    assume_role_for_smtp,
    create_sts_client_with_instance_profile,
    SMTPAssumeRoleException
)


class TestBuildRoleArn:
    """Tests for build_role_arn function"""

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.get_account_id_from_sts')
    def test_build_role_arn_from_name(self, mock_get_account):
        """Test building ARN from role name"""
        mock_get_account.return_value = '123456789012'

        result = build_role_arn('my-test-role')

        assert result == 'arn:aws:iam::123456789012:role/my-test-role'
        mock_get_account.assert_called_once()

    def test_build_role_arn_already_arn(self):
        """Test that existing ARN is returned unchanged"""
        arn = 'arn:aws:iam::123456789012:role/existing-role'

        result = build_role_arn(arn)

        assert result == arn

    def test_build_role_arn_empty_raises(self):
        """Test that empty role name raises exception"""
        with pytest.raises(SMTPAssumeRoleException):
            build_role_arn('')

    def test_build_role_arn_none_raises(self):
        """Test that None role name raises exception"""
        with pytest.raises(SMTPAssumeRoleException):
            build_role_arn(None)


class TestGetAccountIdFromSts:
    """Tests for get_account_id_from_sts function"""

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.create_sts_client_with_instance_profile')
    def test_get_account_id_success(self, mock_create_client):
        """Test successful account ID retrieval"""
        mock_client = mock.Mock()
        mock_client.get_caller_identity.return_value = {'Account': '123456789012'}
        mock_create_client.return_value = mock_client

        result = get_account_id_from_sts()

        assert result == '123456789012'
        mock_client.get_caller_identity.assert_called_once()

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.create_sts_client_with_instance_profile')
    def test_get_account_id_boto_error(self, mock_create_client):
        """Test handling of boto errors"""
        from botocore.exceptions import ClientError

        mock_client = mock.Mock()
        mock_client.get_caller_identity.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            'GetCallerIdentity'
        )
        mock_create_client.return_value = mock_client

        with pytest.raises(SMTPAssumeRoleException):
            get_account_id_from_sts()


class TestAssumeRoleForSmtp:
    """Tests for assume_role_for_smtp function"""

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.build_role_arn')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.create_sts_client_with_instance_profile')
    def test_assume_role_success(self, mock_create_client, mock_build_arn):
        """Test successful role assumption"""
        mock_build_arn.return_value = 'arn:aws:iam::123456789012:role/test-role'

        mock_client = mock.Mock()
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

        assert result['access_key'] == 'AKIATEST123'
        assert result['secret_key'] == 'test-secret-key'
        assert result['session_token'] == 'test-session-token'
        assert result['expiration'] == expiration

        mock_client.assume_role.assert_called_once()
        call_args = mock_client.assume_role.call_args[1]
        assert call_args['RoleArn'] == 'arn:aws:iam::123456789012:role/test-role'
        assert call_args['RoleSessionName'] == 'ckan-ses-session'

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.build_role_arn')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.create_sts_client_with_instance_profile')
    def test_assume_role_custom_session_name(self, mock_create_client, mock_build_arn):
        """Test role assumption with custom session name"""
        mock_build_arn.return_value = 'arn:aws:iam::123456789012:role/test-role'

        mock_client = mock.Mock()
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
        assert call_args['RoleSessionName'] == 'custom-session'

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.build_role_arn')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.create_sts_client_with_instance_profile')
    def test_assume_role_boto_error(self, mock_create_client, mock_build_arn):
        """Test handling of boto errors during assume role"""
        from botocore.exceptions import ClientError

        mock_build_arn.return_value = 'arn:aws:iam::123456789012:role/test-role'

        mock_client = mock.Mock()
        mock_client.assume_role.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied', 'Message': 'Not authorized'}},
            'AssumeRole'
        )
        mock_create_client.return_value = mock_client

        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            assume_role_for_smtp('test-role', 'us-east-1')

        assert 'Failed to assume role' in str(exc_info.value)


class TestCreateStsClientWithInstanceProfile:
    """Tests for create_sts_client_with_instance_profile function"""

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.InstanceMetadataFetcher')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.InstanceMetadataProvider')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.boto3')
    def test_create_sts_client_success(self, mock_boto3, mock_provider_class, mock_fetcher_class):
        """Test successful STS client creation with instance profile"""
        # Mock credentials from instance metadata
        mock_creds = mock.Mock()
        mock_creds.access_key = 'AKIAINSTANCE123'
        mock_creds.secret_key = 'instance-secret-key'
        mock_creds.token = 'instance-session-token'

        mock_provider = mock.Mock()
        mock_provider.load.return_value = mock_creds
        mock_provider_class.return_value = mock_provider

        mock_client = mock.Mock()
        mock_boto3.client.return_value = mock_client

        result = create_sts_client_with_instance_profile()

        assert result == mock_client
        mock_boto3.client.assert_called_once_with(
            'sts',
            aws_access_key_id='AKIAINSTANCE123',
            aws_secret_access_key='instance-secret-key',
            aws_session_token='instance-session-token'
        )

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.InstanceMetadataFetcher')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.InstanceMetadataProvider')
    def test_create_sts_client_no_instance_profile(self, mock_provider_class, mock_fetcher_class):
        """Test error when instance profile is not available"""
        mock_provider = mock.Mock()
        mock_provider.load.side_effect = Exception('Unable to retrieve credentials')
        mock_provider_class.return_value = mock_provider

        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            create_sts_client_with_instance_profile()

        assert 'Failed to create STS client' in str(exc_info.value)

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.InstanceMetadataFetcher')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.InstanceMetadataProvider')
    def test_create_sts_client_credentials_none(self, mock_provider_class, mock_fetcher_class):
        """Test error when instance profile returns None credentials"""
        mock_provider = mock.Mock()
        mock_provider.load.return_value = None
        mock_provider_class.return_value = mock_provider

        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            create_sts_client_with_instance_profile()

        assert 'Failed to load credentials from EC2 instance profile' in str(exc_info.value)


class TestAssumeRoleEdgeCases:
    """Additional edge case tests for assume_role_for_smtp"""

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.build_role_arn')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.smtp_assume_role.create_sts_client_with_instance_profile')
    def test_assume_role_generic_exception(self, mock_create_client, mock_build_arn):
        """Test handling of generic exception during assume role"""
        mock_build_arn.return_value = 'arn:aws:iam::123456789012:role/test-role'

        mock_client = mock.Mock()
        mock_client.assume_role.side_effect = Exception('Unexpected error')
        mock_create_client.return_value = mock_client

        with pytest.raises(SMTPAssumeRoleException) as exc_info:
            assume_role_for_smtp('test-role', 'us-east-1')

        assert 'Unexpected error during SMTP AssumeRole' in str(exc_info.value)
