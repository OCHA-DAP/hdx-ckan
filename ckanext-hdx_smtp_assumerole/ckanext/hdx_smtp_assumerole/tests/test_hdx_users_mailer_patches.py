# encoding: utf-8

import pytest
import mock
from email.header import Header
import ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches as patches_module
from ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches import (
    _get_decoded_str,
    is_patched,
    patch_hdx_users_mailer,
    unpatch_hdx_users_mailer,
    patched_mail_recipient_html
)
from ckanext.hdx_smtp_assumerole.helpers.caching import SESAssumeRoleException


class TestGetDecodedStr:
    """Tests for _get_decoded_str helper function"""

    def test_decode_simple_string(self):
        """Test decoding a simple ASCII string"""
        result = _get_decoded_str('John Doe')
        assert result == 'John Doe'

    def test_decode_empty_string(self):
        """Test decoding an empty string"""
        result = _get_decoded_str('')
        assert result == ''

    def test_decode_none(self):
        """Test decoding None"""
        result = _get_decoded_str(None)
        assert result == ''

    def test_decode_utf8_string(self):
        """Test decoding a UTF-8 string"""
        result = _get_decoded_str('François Müller')
        assert result == 'François Müller'

    def test_decode_encoded_header(self):
        """Test decoding an encoded email header"""
        # Create an encoded header
        encoded = str(Header('Test User', 'utf-8'))
        result = _get_decoded_str(encoded)
        assert 'Test' in result

    def test_decode_bytes_without_charset(self):
        """Test decoding when Header.decode_header returns bytes with no charset."""
        with mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.Header') as mock_header_cls:
            mock_header_cls.return_value.decode_header.return_value = [(b'raw bytes', None)]
            result = _get_decoded_str('anything')
        assert result == 'raw bytes'

    def test_decode_exception_returns_original(self):
        """Test that a decode error returns the original display_name unchanged."""
        with mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.Header') as mock_header_cls:
            mock_header_cls.side_effect = Exception('decode error')
            result = _get_decoded_str('fallback name')
        assert result == 'fallback name'


class TestPatchFunctions:
    """Tests for patch/unpatch functions"""

    def setup_method(self):
        """Reset patching state before each test"""
        # Reset module state
        patches_module._patches_applied = False
        patches_module._original_mail_recipient_html = None

    def test_is_patched_initially_false(self):
        """Test that is_patched returns False initially"""
        assert not is_patched()

    def test_patch_hdx_users_mailer_no_module(self):
        """Test patching when hdx_users module is not available"""
        # Mock the import to raise ImportError
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if 'ckanext.hdx_users' in name:
                raise ImportError('No module named ckanext.hdx_users')
            return original_import(name, *args, **kwargs)

        # Reset state to ensure clean test
        patches_module._patches_applied = False

        with mock.patch('builtins.__import__', side_effect=mock_import):
            # This should handle ImportError gracefully
            patch_hdx_users_mailer()
            # Should not raise exception, just log warning
            assert not is_patched()

    def test_patch_hdx_users_mailer_idempotent(self):
        """Test that patching multiple times is safe"""
        patches_module._patches_applied = True

        # Second call should return early
        patch_hdx_users_mailer()
        assert is_patched()

    def test_unpatch_when_not_patched(self):
        """Test unpatching when patches are not applied"""
        # Should not raise exception
        unpatch_hdx_users_mailer()
        assert not is_patched()

    def test_unpatch_no_module(self):
        """Test unpatching when hdx_users module is not available"""
        patches_module._patches_applied = True

        # Should handle ImportError gracefully
        unpatch_hdx_users_mailer()


class TestPatchedMailRecipientHtml:
    """Tests for patched_mail_recipient_html function"""

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.tk')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.get_cached_ses_credentials')
    def test_basic_send(self, mock_get_creds, mock_tk, mock_send):
        """Test basic email sending with recipients"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_tk.config = {'smtp.mail_from': 'hdx@example.com', 'ckan.site_url': 'https://data.example.com'}
        mock_tk.render.return_value = '<html><body>Email body</body></html>'

        patched_mail_recipient_html(
            sender_name='Test Sender',
            sender_email='sender@example.com',
            recipients_list=[{'email': 'user@example.com', 'display_name': 'Test User'}],
            subject='Test Subject',
            content_dict={'message': 'Hello'}
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['smtp_from'] == 'hdx@example.com'
        assert call_args['recipients'] == ['user@example.com']
        assert call_args['subject'] == 'Test Subject'
        assert call_args['access_key'] == 'AKIATEST'

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.tk')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.get_cached_ses_credentials')
    def test_with_cc_and_bcc(self, mock_get_creds, mock_tk, mock_send):
        """Test email sending with CC and BCC recipients"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_tk.config = {'smtp.mail_from': 'hdx@example.com', 'ckan.site_url': 'https://data.example.com'}
        mock_tk.render.return_value = '<html><body>Email</body></html>'

        patched_mail_recipient_html(
            recipients_list=[{'email': 'to@example.com', 'display_name': 'To User'}],
            subject='Test CC/BCC',
            content_dict={'message': 'Hello'},
            cc_recipients_list=[{'email': 'cc@example.com', 'display_name': 'CC User'}],
            bcc_recipients_list=[{'email': 'bcc@example.com', 'display_name': 'BCC User'}]
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert 'to@example.com' in call_args['recipients']
        assert 'cc@example.com' in call_args['recipients']
        assert 'bcc@example.com' in call_args['recipients']

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.tk')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.get_cached_ses_credentials')
    def test_with_multiple_recipients(self, mock_get_creds, mock_tk, mock_send):
        """Test email sending with multiple To recipients"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_tk.config = {'smtp.mail_from': 'hdx@example.com', 'ckan.site_url': 'https://data.example.com'}
        mock_tk.render.return_value = '<html><body>Email</body></html>'

        patched_mail_recipient_html(
            recipients_list=[
                {'email': 'user1@example.com', 'display_name': 'User One'},
                {'email': 'user2@example.com'}
            ],
            subject='Multi Recipients',
            content_dict={'message': 'Hello all'}
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert 'user1@example.com' in call_args['recipients']
        assert 'user2@example.com' in call_args['recipients']

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.tk')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.get_cached_ses_credentials')
    def test_with_file_attachment(self, mock_get_creds, mock_tk, mock_send):
        """Test email sending with file attachment (cgi.FieldStorage)"""
        import io
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_tk.config = {'smtp.mail_from': 'hdx@example.com', 'ckan.site_url': 'https://data.example.com'}
        mock_tk.render.return_value = '<html><body>Email</body></html>'

        # Mock a cgi.FieldStorage object
        import cgi
        mock_file = mock.Mock(spec=cgi.FieldStorage)
        mock_file.file = io.BytesIO(b'file content')
        mock_file.filename = 'report.csv'

        patched_mail_recipient_html(
            recipients_list=[{'email': 'user@example.com', 'display_name': 'User'}],
            subject='With Attachment',
            content_dict={'message': 'See attached'},
            file=mock_file
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        assert call_args['mime_message'] is not None
        msg_string = call_args['mime_message'].as_string()
        assert 'attachment' in msg_string
        assert 'csv' in msg_string

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.get_cached_ses_credentials')
    def test_credential_failure_raises(self, mock_get_creds):
        """Test that credential loading failure raises exception"""
        mock_get_creds.side_effect = SESAssumeRoleException('Cannot assume role')

        with pytest.raises(SESAssumeRoleException) as exc_info:
            patched_mail_recipient_html(
                recipients_list=[{'email': 'user@example.com'}],
                subject='Test',
                content_dict={'message': 'Hello'}
            )

        assert 'Cannot assume role' in str(exc_info.value)

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.tk')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.get_cached_ses_credentials')
    def test_ses_send_failure_raises(self, mock_get_creds, mock_tk, mock_send):
        """Test that SES send failure propagates exception"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_tk.config = {'smtp.mail_from': 'hdx@example.com', 'ckan.site_url': 'https://data.example.com'}
        mock_tk.render.return_value = '<html><body>Email</body></html>'
        mock_send.side_effect = Exception('SES API Error')

        with pytest.raises(Exception) as exc_info:
            patched_mail_recipient_html(
                recipients_list=[{'email': 'user@example.com'}],
                subject='Test',
                content_dict={'message': 'Hello'}
            )

        assert 'SES API Error' in str(exc_info.value)

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.send_email_via_ses')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.tk')
    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.hdx_users_mailer_patches.get_cached_ses_credentials')
    def test_custom_headers(self, mock_get_creds, mock_tk, mock_send):
        """Test email sending with custom headers"""
        mock_get_creds.return_value = {
            'access_key': 'AKIATEST',
            'secret_key': 'test-secret',
            'session_token': 'test-token',
            'region': 'us-east-1'
        }
        mock_tk.config = {'smtp.mail_from': 'hdx@example.com', 'ckan.site_url': 'https://data.example.com'}
        mock_tk.render.return_value = '<html><body>Email</body></html>'

        patched_mail_recipient_html(
            recipients_list=[{'email': 'user@example.com', 'display_name': 'User'}],
            subject='Test Headers',
            content_dict={'message': 'Hello'},
            headers={'X-Custom': 'custom-value'}
        )

        mock_send.assert_called_once()
        call_args = mock_send.call_args[1]
        msg = call_args['mime_message']
        assert msg['X-Custom'] == 'custom-value'
