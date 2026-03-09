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
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_plain_text(self, mock_get_creds, mock_send):
        """Test sending plain text email via patched_mail_user"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User',
            'name': 'testuser'
        }

        patched_mail_user(
            recipient=user,
            subject='Test Subject',
            body='Plain text body'
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == ['user@example.com']
        assert call_args['subject'] == 'Test Subject'
        assert call_args['body'] == 'Plain text body'
        assert 'To' in call_args['headers']

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_with_html(self, mock_get_creds, mock_send):
        """Test sending HTML email via patched_mail_user"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User',
            'name': 'testuser',
        }

        patched_mail_user(
            recipient=user,
            subject='Test Subject',
            body='Plain text',
            body_html='<html><body>HTML body</body></html>'
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert 'mime_message' in call_args
        assert call_args['mime_message'] is not None

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_html_only(self, mock_get_creds, mock_send):
        """Test sending HTML-only email (no plain text)"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User',
            'name': 'testuser',
        }

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
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_with_attachments(self, mock_get_creds, mock_send):
        """Test sending email with attachments"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User',
            'name': 'testuser',
        }

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
        mime_msg = call_args['mime_message']
        assert mime_msg is not None

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_with_custom_headers(self, mock_get_creds, mock_send):
        """Test sending email with custom headers"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User',
            'name': 'testuser',
        }

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
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_recipient_as_dict(self, mock_get_creds, mock_send):
        """Test patched_mail_user with recipient as dict (not User object)"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

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

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_no_credentials_raises(self, mock_get_creds):
        """Test that credential loading failure raises exception"""
        from ckanext.hdx_smtp_assumerole.helpers.caching import SESAssumeRoleException
        mock_get_creds.side_effect = SESAssumeRoleException('Failed to load credentials')

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User',
            'name': 'testuser',
        }

        with pytest.raises(SESAssumeRoleException) as exc_info:
            patched_mail_user(
                recipient=user,
                subject='Test',
                body='Body'
            )

        assert 'Failed to load credentials' in str(exc_info.value)

    # patched_mail_recipient tests
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_recipient_plain_text(self, mock_get_creds, mock_send):
        """Test patched_mail_recipient with plain text"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

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
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_recipient_with_html(self, mock_get_creds, mock_send):
        """Test patched_mail_recipient with HTML"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

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
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_recipient_with_attachments(self, mock_get_creds, mock_send):
        """Test patched_mail_recipient with attachments"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

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

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_recipient_no_credentials_raises(self, mock_get_creds):
        """Test that credential loading failure raises exception"""
        from ckanext.hdx_smtp_assumerole.helpers.caching import SESAssumeRoleException
        mock_get_creds.side_effect = SESAssumeRoleException('Failed to load credentials')

        with pytest.raises(SESAssumeRoleException) as exc_info:
            patched_mail_recipient(
                recipient_name='Test',
                recipient_email='user@example.com',
                subject='Test',
                body='Body'
            )

        assert 'Failed to load credentials' in str(exc_info.value)

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

        assert msg.is_multipart()
        msg_string = msg.as_string()
        assert 'test.txt' in msg_string

    def test_build_mime_message_attachment_auto_detect_media_type(self):
        """Test _build_mime_message_with_attachments auto-detects media type"""
        file_obj = BytesIO(b'PDF content')
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


class TestTokenExpirationHelperPatch:
    """
    Tests that patch/unpatch_mailer_functions correctly patch token_expiration_helper._mail_recipient.

    token_expiration_helper captures tk.mail_recipient at module load time:
        _mail_recipient = tk.mail_recipient
    so it must be explicitly patched by name after the module is imported, otherwise
    the cron job that sends expiration warning emails will use the original SMTP path
    instead of SES, causing failures when SMTP credentials (from AssumeRole) have expired.
    """

    def setup_method(self):
        """Reset patching state before each test"""
        import ckanext.hdx_smtp_assumerole.helpers.mailer_patches as pm
        pm._patches_applied = False
        pm._original_mail_user = None
        pm._original_mail_recipient = None

    def teardown_method(self):
        """Ensure patches are removed after each test"""
        if is_patched():
            unpatch_mailer_functions()

    def test_patch_replaces_token_expiration_helper_mail_recipient(self):
        """After patch_mailer_functions(), token_expiration_helper._mail_recipient must use SES"""
        from ckanext.hdx_users.helpers import token_expiration_helper

        patch_mailer_functions()

        assert token_expiration_helper._mail_recipient is patched_mail_recipient

    def test_unpatch_restores_token_expiration_helper_mail_recipient(self):
        """After unpatch_mailer_functions(), token_expiration_helper._mail_recipient must be restored"""
        from ckanext.hdx_users.helpers import token_expiration_helper
        original_ref = token_expiration_helper._mail_recipient

        patch_mailer_functions()
        unpatch_mailer_functions()

        assert token_expiration_helper._mail_recipient is original_ref

    def test_patch_handles_import_error_gracefully(self):
        """patch_mailer_functions() must complete successfully even if token_expiration_helper is absent"""
        import sys
        import ckanext.hdx_users.helpers as helpers_pkg

        key = 'ckanext.hdx_users.helpers.token_expiration_helper'
        saved_module = sys.modules.pop(key, None)
        saved_attr = getattr(helpers_pkg, 'token_expiration_helper', None)
        if saved_attr is not None:
            delattr(helpers_pkg, 'token_expiration_helper')
        # Setting to None blocks 'from package import module' with ImportError
        sys.modules[key] = None

        try:
            patch_mailer_functions()  # Must not raise
            assert is_patched()
        finally:
            del sys.modules[key]
            if saved_module is not None:
                sys.modules[key] = saved_module
            if saved_attr is not None:
                helpers_pkg.token_expiration_helper = saved_attr

    def test_unpatch_handles_import_error_gracefully(self):
        """unpatch_mailer_functions() must complete successfully even if token_expiration_helper is absent"""
        import sys
        import ckanext.hdx_users.helpers as helpers_pkg

        patch_mailer_functions()

        key = 'ckanext.hdx_users.helpers.token_expiration_helper'
        saved_module = sys.modules.pop(key, None)
        saved_attr = getattr(helpers_pkg, 'token_expiration_helper', None)
        # Capture _mail_recipient before we block the import — unpatch will fail with
        # ImportError and won't restore it, so we must do it explicitly in finally.
        saved_mail_recipient = getattr(saved_attr, '_mail_recipient', None) if saved_attr is not None else None
        if saved_attr is not None:
            delattr(helpers_pkg, 'token_expiration_helper')
        sys.modules[key] = None

        try:
            unpatch_mailer_functions()  # Must not raise
            assert not is_patched()
        finally:
            del sys.modules[key]
            if saved_module is not None:
                sys.modules[key] = saved_module
            if saved_attr is not None:
                helpers_pkg.token_expiration_helper = saved_attr
                # unpatch couldn't reach the module; restore _mail_recipient manually
                if saved_mail_recipient is not None:
                    saved_attr._mail_recipient = saved_mail_recipient

    def test_patch_handles_unexpected_exception_gracefully(self):
        """patch_mailer_functions() must log warning and still set is_patched()=True when
        patching token_expiration_helper raises a non-ImportError exception.

        Strategy: replace the module on the package with a BadModule whose __setattr__
        raises RuntimeError. CPython's 'from package import name' checks hasattr(package, name)
        first, so it returns BadModule without hitting sys.modules. The subsequent attribute
        assignment triggers the exception that must be caught by 'except Exception as e'.
        """
        import ckanext.hdx_users.helpers as helpers_pkg

        try:
            from ckanext.hdx_users.helpers import token_expiration_helper as real_helper
        except ImportError:
            pytest.skip('token_expiration_helper not available')

        class BadModule:
            def __setattr__(self, name, value):
                raise RuntimeError(f'Simulated unexpected error setting {name}')

        bad_module = BadModule()
        saved_attr = helpers_pkg.token_expiration_helper
        # Capture before patching — must be unchanged after the failed assignment
        mail_recipient_before = real_helper._mail_recipient

        helpers_pkg.token_expiration_helper = bad_module
        try:
            patch_mailer_functions()  # Must not raise
            assert is_patched()
            # bad_module.__setattr__ raised, so real_helper was never touched
            assert real_helper._mail_recipient is mail_recipient_before
        finally:
            helpers_pkg.token_expiration_helper = saved_attr

    def test_unpatch_handles_unexpected_exception_gracefully(self):
        """unpatch_mailer_functions() must log warning and still set is_patched()=False when
        restoring token_expiration_helper raises a non-ImportError exception.

        patch_mailer_functions() runs first with the real module so the initial patch
        succeeds. Then BadModule is swapped in so that the restore assignment in
        unpatch_mailer_functions() triggers the RuntimeError that must be caught.
        The finally block explicitly restores real_helper._mail_recipient to avoid
        state leaking into subsequent tests.
        """
        import ckanext.hdx_users.helpers as helpers_pkg

        try:
            from ckanext.hdx_users.helpers import token_expiration_helper as real_helper
        except ImportError:
            pytest.skip('token_expiration_helper not available')

        original_mail_recipient_ref = real_helper._mail_recipient

        patch_mailer_functions()
        # At this point real_helper._mail_recipient == patched_mail_recipient

        class BadModule:
            def __setattr__(self, name, value):
                raise RuntimeError(f'Simulated unexpected error restoring {name}')

        bad_module = BadModule()
        saved_attr = helpers_pkg.token_expiration_helper

        helpers_pkg.token_expiration_helper = bad_module
        try:
            unpatch_mailer_functions()  # Must not raise
            assert not is_patched()
        finally:
            helpers_pkg.token_expiration_helper = saved_attr
            # unpatch failed for this module, restore _mail_recipient explicitly
            real_helper._mail_recipient = original_mail_recipient_ref


class TestMailerPatchesErrorHandling:
    """Tests for error handling in mailer_patches"""

    def teardown_method(self):
        """Ensure patches are removed after each test"""
        if is_patched():
            unpatch_mailer_functions()

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_missing_email(self, mock_get_creds, mock_send):
        """Test error handling when recipient has no email"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

        user = {
            'display_name': 'Test User',
            'name': 'testuser'
        }

        patched_mail_user(
            recipient=user,
            subject='Test',
            body='Body'
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['recipients'] == [None]

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_ses_error_propagates(self, mock_get_creds, mock_send):
        """Test that SES errors are propagated to caller"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

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
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_recipient_empty_email(self, mock_get_creds, mock_send):
        """Test error handling with empty email string"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

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
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_large_attachment(self, mock_get_creds, mock_send):
        """Test handling of large attachments (edge case)"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User'
        }

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
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_multiple_attachments(self, mock_get_creds, mock_send):
        """Test handling multiple attachments"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

        user = {
            'email': 'user@example.com',
            'display_name': 'Test User'
        }

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

        assert 'file1.txt' in msg_string
        assert 'file2.pdf' in msg_string
        assert 'file3.jpg' in msg_string

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_user_special_chars_in_headers(self, mock_get_creds, mock_send):
        """Test handling of special characters in email headers"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

        user = {
            'email': 'user@example.com',
            'display_name': 'Test Üser with Spëcial Chàrs'
        }

        patched_mail_user(
            recipient=user,
            subject='Subject with 🎉 émojis and special chars',
            body='Body with special chars: ñ, ü, é, 🌍'
        )

        mock_send.assert_called_once()

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    def test_patched_mail_recipient_none_recipient_name(self, mock_get_creds, mock_send):
        """Test mail_recipient with None as recipient name"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

        patched_mail_recipient(
            recipient_name=None,
            recipient_email='user@example.com',
            subject='Test',
            body='Body'
        )

        mock_send.assert_called_once()

    def test_build_mime_with_attachment_no_media_type(self):
        """Test MIME building with attachment without explicit media type"""
        file_obj = BytesIO(b'Test content')
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
        assert 'application/octet-stream' in msg_string

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.get_ses_credentials')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.mailer_patches.tk')
    def test_patched_mail_user_missing_mail_from_config(self, mock_tk, mock_get_creds, mock_send):
        """Test behavior when mail_from config is missing"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }

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
        assert call_args['smtp_from'] is None
