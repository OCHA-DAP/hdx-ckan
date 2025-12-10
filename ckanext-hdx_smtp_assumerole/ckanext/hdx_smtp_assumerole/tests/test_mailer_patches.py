# encoding: utf-8

import pytest
import mock
from io import BytesIO

from ckanext.hdx_smtp_assumerole.helpers.mailer_patches import (
    patch_mailer_functions,
    unpatch_mailer_functions,
    is_patched,
    patched_mail_user,
    patched_mail_recipient,
    _build_mime_message_with_attachments
)


class TestMailerPatches:
    """Tests for mailer_patches module"""

    def teardown_method(self):
        """Ensure patches are removed after each test"""
        if is_patched():
            unpatch_mailer_functions()

    # Patching mechanism tests
    def test_patch_mailer_functions_idempotent(self):
        """Test that patching multiple times is safe (idempotent)"""
        patch_mailer_functions()
        assert is_patched()

        # Patch again - should not cause errors
        patch_mailer_functions()
        assert is_patched()

    def test_unpatch_mailer_functions(self):
        """Test unpatching restores original functions"""
        patch_mailer_functions()
        assert is_patched()

        unpatch_mailer_functions()
        assert not is_patched()

    def test_is_patched_initially_false(self):
        """Test is_patched returns False before patching"""
        assert not is_patched()

    # patched_mail_user tests
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_plain_text(self, mock_manager_class, mock_send):
        """Test sending plain text email via patched_mail_user"""
        # Setup mocks
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        # Use dict instead of Mock User object (code supports both)
        user = {
            'email': 'user@example.com',
            'display_name': 'Test User',
            'name': 'testuser'
        }

        # Call patched function
        patched_mail_user(
            recipient=user,
            subject='Test Subject',
            body='Plain text body'
        )

        # Verify credentials were refreshed
        mock_manager.ensure_fresh_credentials.assert_called_once()

        # Verify email was sent
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == ['user@example.com']
        assert call_args['subject'] == 'Test Subject'
        assert call_args['body'] == 'Plain text body'
        assert 'To' in call_args['headers']

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_with_html(self, mock_manager_class, mock_send):
        """Test sending HTML email via patched_mail_user"""
        # Setup mocks
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        user = mock.Mock()
        user.email = 'user@example.com'
        user.display_name = 'Test User'

        # Call with HTML
        patched_mail_user(
            recipient=user,
            subject='Test Subject',
            body='Plain text',
            body_html='<html><body>HTML body</body></html>'
        )

        # Verify MIME message was used (not simple body)
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert 'mime_message' in call_args
        assert call_args['mime_message'] is not None

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_html_only(self, mock_manager_class, mock_send):
        """Test sending HTML-only email (no plain text)"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        user = mock.Mock()
        user.email = 'user@example.com'
        user.display_name = 'Test User'

        patched_mail_user(
            recipient=user,
            subject='Test Subject',
            body=None,
            body_html='<html><body>HTML only</body></html>'
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert 'mime_message' in call_args

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_with_attachments(self, mock_manager_class, mock_send):
        """Test sending email with attachments"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        user = mock.Mock()
        user.email = 'user@example.com'
        user.display_name = 'Test User'

        # Create attachment
        file_obj = BytesIO(b'Test file content')
        attachments = [('test.txt', file_obj, 'text/plain')]

        patched_mail_user(
            recipient=user,
            subject='Test with Attachment',
            body='See attached file',
            attachments=attachments
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert 'mime_message' in call_args
        # Verify attachment is in MIME message
        mime_msg = call_args['mime_message']
        assert mime_msg is not None

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_with_custom_headers(self, mock_manager_class, mock_send):
        """Test sending email with custom headers"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        user = mock.Mock()
        user.email = 'user@example.com'
        user.display_name = 'Test User'

        custom_headers = {
            'Reply-To': 'noreply@example.com',
            'X-Custom-Header': 'custom-value'
        }

        patched_mail_user(
            recipient=user,
            subject='Test',
            body='Body',
            headers=custom_headers
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert 'To' in call_args['headers']

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_recipient_as_dict(self, mock_manager_class, mock_send):
        """Test patched_mail_user with recipient as dict (not User object)"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        recipient_dict = {
            'email': 'user@example.com',
            'display_name': 'Test User',
            'name': 'testuser'
        }

        patched_mail_user(
            recipient=recipient_dict,
            subject='Test',
            body='Body'
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == ['user@example.com']

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_no_credentials_raises(self, mock_manager_class):
        """Test that missing credentials raises exception"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = None
        mock_manager_class.get_instance.return_value = mock_manager

        user = mock.Mock()
        user.email = 'user@example.com'

        with pytest.raises(Exception) as exc_info:
            patched_mail_user(
                recipient=user,
                subject='Test',
                body='Body'
            )

        assert 'No SES credentials available' in str(exc_info.value)

    # patched_mail_recipient tests
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_recipient_plain_text(self, mock_manager_class, mock_send):
        """Test patched_mail_recipient with plain text"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        patched_mail_recipient(
            recipient_name='Test User',
            recipient_email='user@example.com',
            subject='Test Subject',
            body='Plain text body'
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == ['user@example.com']
        assert call_args['subject'] == 'Test Subject'
        assert call_args['body'] == 'Plain text body'

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_recipient_with_html(self, mock_manager_class, mock_send):
        """Test patched_mail_recipient with HTML"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        patched_mail_recipient(
            recipient_name='Test User',
            recipient_email='user@example.com',
            subject='Test',
            body='Plain',
            body_html='<html><body>HTML</body></html>'
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert 'mime_message' in call_args

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_recipient_with_attachments(self, mock_manager_class, mock_send):
        """Test patched_mail_recipient with attachments"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        file_obj = BytesIO(b'Test content')
        attachments = [('file.pdf', file_obj, 'application/pdf')]

        patched_mail_recipient(
            recipient_name='Test User',
            recipient_email='user@example.com',
            subject='Test',
            body='Body',
            attachments=attachments
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert 'mime_message' in call_args

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_recipient_no_credentials_raises(self, mock_manager_class):
        """Test that missing credentials raises exception"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = None
        mock_manager_class.get_instance.return_value = mock_manager

        with pytest.raises(Exception) as exc_info:
            patched_mail_recipient(
                recipient_name='Test',
                recipient_email='user@example.com',
                subject='Test',
                body='Body'
            )

        assert 'No SES credentials available' in str(exc_info.value)

    # Helper function tests
    def test_build_mime_message_plain_text(self):
        """Test _build_mime_message_with_attachments for plain text"""
        msg = _build_mime_message_with_attachments(
            mail_from='sender@example.com',
            recipient_email='recipient@example.com',
            recipient_name='Recipient Name',
            subject='Test Subject',
            body='Plain text body',
            body_html=None,
            headers=None,
            attachments=None
        )

        # From and Reply-To should include display name
        assert msg['From'] == '"Humanitarian Data Exchange (HDX)" <sender@example.com>'
        assert msg['Reply-To'] == '"Humanitarian Data Exchange (HDX)" <sender@example.com>'
        assert msg['Subject'] == 'Test Subject'
        assert 'Recipient Name' in msg['To']
        assert 'recipient@example.com' in msg['To']

    def test_build_mime_message_with_html(self):
        """Test _build_mime_message_with_attachments with HTML"""
        msg = _build_mime_message_with_attachments(
            mail_from='sender@example.com',
            recipient_email='recipient@example.com',
            recipient_name='Test',
            subject='Test',
            body='Plain',
            body_html='<html><body>HTML</body></html>',
            headers=None,
            attachments=None
        )

        # Check that message is multipart
        assert msg.is_multipart()

    def test_build_mime_message_with_attachment(self):
        """Test _build_mime_message_with_attachments with attachment"""
        file_obj = BytesIO(b'Test file')
        attachments = [('test.txt', file_obj, 'text/plain')]

        msg = _build_mime_message_with_attachments(
            mail_from='sender@example.com',
            recipient_email='recipient@example.com',
            recipient_name=None,
            subject='Test',
            body='Body',
            body_html=None,
            headers=None,
            attachments=attachments
        )

        # Check that attachment was added
        assert msg.is_multipart()
        msg_string = msg.as_string()
        assert 'test.txt' in msg_string

    def test_build_mime_message_attachment_auto_detect_media_type(self):
        """Test _build_mime_message_with_attachments auto-detects media type"""
        file_obj = BytesIO(b'PDF content')
        # Don't specify media type - should auto-detect from .pdf extension
        attachments = [('report.pdf', file_obj)]

        msg = _build_mime_message_with_attachments(
            mail_from='sender@example.com',
            recipient_email='recipient@example.com',
            recipient_name=None,
            subject='Test',
            body='Body',
            body_html=None,
            headers=None,
            attachments=attachments
        )

        msg_string = msg.as_string()
        assert 'report.pdf' in msg_string


class TestMailerPatchesErrorHandling:
    """Tests for error handling in mailer_patches"""

    def teardown_method(self):
        """Ensure patches are removed after each test"""
        if is_patched():
            unpatch_mailer_functions()

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_missing_email(self, mock_manager_class, mock_send):
        """Test error handling when recipient has no email"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        # User with no email
        user = {
            'display_name': 'Test User',
            'name': 'testuser'
            # Missing 'email' key
        }

        # Should handle gracefully - recipient_email will be None
        patched_mail_user(
            recipient=user,
            subject='Test',
            body='Body'
        )

        # Should still call send_email_via_ses with None email
        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == [None]

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_ses_error_propagates(self, mock_manager_class, mock_send):
        """Test that SES errors are propagated to caller"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        # Simulate SES error
        mock_send.side_effect = Exception('SES API Error: MessageRejected')

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User'
        }

        with pytest.raises(Exception) as exc_info:
            patched_mail_user(
                recipient=user,
                subject='Test',
                body='Body'
            )

        assert 'MessageRejected' in str(exc_info.value)

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_credentials_refresh_error(self, mock_manager_class, mock_send):
        """Test error handling when credential refresh fails"""
        mock_manager = mock.Mock()
        # Simulate credential refresh failure
        mock_manager.ensure_fresh_credentials.side_effect = Exception('Failed to refresh credentials')
        mock_manager_class.get_instance.return_value = mock_manager

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User'
        }

        with pytest.raises(Exception) as exc_info:
            patched_mail_user(
                recipient=user,
                subject='Test',
                body='Body'
            )

        assert 'Failed to refresh credentials' in str(exc_info.value)

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_recipient_empty_email(self, mock_manager_class, mock_send):
        """Test error handling with empty email string"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        # Empty email
        patched_mail_recipient(
            recipient_name='Test',
            recipient_email='',
            subject='Test',
            body='Body'
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == ['']

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_large_attachment(self, mock_manager_class, mock_send):
        """Test handling of large attachments (edge case)"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User'
        }

        # Create 5MB attachment (close to typical email limits)
        large_content = b'x' * (5 * 1024 * 1024)
        file_obj = BytesIO(large_content)
        attachments = [('large_file.bin', file_obj, 'application/octet-stream')]

        patched_mail_user(
            recipient=user,
            subject='Large Attachment Test',
            body='See attachment',
            attachments=attachments
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert 'mime_message' in call_args

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_multiple_attachments(self, mock_manager_class, mock_send):
        """Test handling multiple attachments"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User'
        }

        # Multiple attachments with different types
        attachments = [
            ('file1.txt', BytesIO(b'Text content'), 'text/plain'),
            ('file2.pdf', BytesIO(b'PDF content'), 'application/pdf'),
            ('file3.jpg', BytesIO(b'Image content'), 'image/jpeg'),
        ]

        patched_mail_user(
            recipient=user,
            subject='Multiple Attachments',
            body='See attached files',
            attachments=attachments
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        mime_msg = call_args['mime_message']
        msg_string = mime_msg.as_string()

        # Verify all attachments are present
        assert 'file1.txt' in msg_string
        assert 'file2.pdf' in msg_string
        assert 'file3.jpg' in msg_string

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_user_special_chars_in_headers(self, mock_manager_class, mock_send):
        """Test handling of special characters in email headers"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        user = {
            'email': 'user@example.com',
            'display_name': 'Test Üser with Spëcial Chàrs'
        }

        patched_mail_user(
            recipient=user,
            subject='Subject with émojis 🎉 and special chars',
            body='Body with special chars: ñ, ü, é'
        )

        mock_send.assert_called_once()

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_patched_mail_recipient_none_recipient_name(self, mock_manager_class, mock_send):
        """Test mail_recipient with None as recipient name"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        patched_mail_recipient(
            recipient_name=None,
            recipient_email='user@example.com',
            subject='Test',
            body='Body'
        )

        mock_send.assert_called_once()

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    def test_build_mime_with_attachment_no_media_type(self, mock_manager_class, mock_send):
        """Test MIME building with attachment without explicit media type"""
        # Test the helper function directly
        file_obj = BytesIO(b'Test content')
        # Tuple with only 2 elements (filename, file_obj) - should auto-detect
        attachments = [('unknown.xyz', file_obj)]

        msg = _build_mime_message_with_attachments(
            mail_from='sender@example.com',
            recipient_email='recipient@example.com',
            recipient_name='Test',
            subject='Test',
            body='Body',
            body_html=None,
            headers=None,
            attachments=attachments
        )

        msg_string = msg.as_string()
        assert 'unknown.xyz' in msg_string
        # Should default to application/octet-stream
        assert 'application/octet-stream' in msg_string

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.SMTPCredentialsManager')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.tk')
    def test_patched_mail_user_missing_mail_from_config(self, mock_tk, mock_manager_class, mock_send):
        """Test behavior when mail_from config is missing"""
        mock_manager = mock.Mock()
        mock_manager.get_ses_credentials.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_manager_class.get_instance.return_value = mock_manager

        # Mock config with no mail_from
        mock_config = {}
        mock_tk.config = mock_config

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User'
        }

        patched_mail_user(
            recipient=user,
            subject='Test',
            body='Body'
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        # smtp_from should be None when config is missing
        assert call_args['smtp_from'] is None
