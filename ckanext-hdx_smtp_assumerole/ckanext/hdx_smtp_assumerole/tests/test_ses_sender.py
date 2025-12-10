# encoding: utf-8

import pytest
import mock
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from ckanext.hdx_smtp_assumerole.helpers.ses_sender import send_email_via_ses


class TestSendEmailViaSes:
    """Tests for send_email_via_ses function"""

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.ses_sender.boto3')
    def test_send_email_success(self, mock_boto3):
        """Test successful email sending via SES API"""
        mock_client = mock.Mock()
        mock_client.send_raw_email.return_value = {
            'MessageId': '0100018d1234abcd-12345678-1234-1234-1234-123456789abc-000000'
        }
        mock_boto3.client.return_value = mock_client

        result = send_email_via_ses(
            smtp_from='sender@example.com',
            recipients=['recipient@example.com'],
            subject='Test Subject',
            body='Test body',
            access_key='AKIATEST123',
            secret_key='test-secret',
            session_token='test-token',
            region='us-east-1'
        )

        # Verify boto3 client was created correctly
        mock_boto3.client.assert_called_once_with(
            'ses',
            aws_access_key_id='AKIATEST123',
            aws_secret_access_key='test-secret',
            aws_session_token='test-token',
            region_name='us-east-1'
        )

        # Verify send_raw_email was called
        mock_client.send_raw_email.assert_called_once()
        call_args = mock_client.send_raw_email.call_args[1]
        assert call_args['Source'] == 'sender@example.com'
        assert call_args['Destinations'] == ['recipient@example.com']

        # Verify result
        assert result['MessageId'] == '0100018d1234abcd-12345678-1234-1234-1234-123456789abc-000000'

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.ses_sender.boto3')
    def test_send_email_with_html(self, mock_boto3):
        """Test sending email with HTML body"""
        mock_client = mock.Mock()
        mock_client.send_raw_email.return_value = {'MessageId': 'test-message-id'}
        mock_boto3.client.return_value = mock_client

        send_email_via_ses(
            smtp_from='sender@example.com',
            recipients=['recipient@example.com'],
            subject='Test Subject',
            body='Plain text body',
            body_html='<html><body>HTML body</body></html>',
            access_key='AKIATEST123',
            secret_key='test-secret',
            session_token='test-token',
            region='us-east-1'
        )

        # Verify send_raw_email was called
        mock_client.send_raw_email.assert_called_once()

        # Verify message has both plain and HTML parts (check MIME structure)
        call_args = mock_client.send_raw_email.call_args[1]
        raw_message = call_args['RawMessage']['Data']
        # Content is base64 encoded, so check for MIME multipart/alternative structure
        assert 'Content-Type: multipart/alternative' in raw_message
        assert 'Content-Type: text/plain' in raw_message
        assert 'Content-Type: text/html' in raw_message

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.ses_sender.boto3')
    def test_send_email_html_only(self, mock_boto3):
        """Test sending email with HTML body only (no plain text)"""
        mock_client = mock.Mock()
        mock_client.send_raw_email.return_value = {'MessageId': 'test-message-id'}
        mock_boto3.client.return_value = mock_client

        send_email_via_ses(
            smtp_from='sender@example.com',
            recipients=['recipient@example.com'],
            subject='Test Subject',
            body=None,
            body_html='<html><body>HTML body</body></html>',
            access_key='AKIATEST123',
            secret_key='test-secret',
            session_token='test-token',
            region='us-east-1'
        )

        # Verify send_raw_email was called
        mock_client.send_raw_email.assert_called_once()

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.ses_sender.boto3')
    def test_send_email_multiple_recipients(self, mock_boto3):
        """Test sending email to multiple recipients"""
        mock_client = mock.Mock()
        mock_client.send_raw_email.return_value = {'MessageId': 'test-message-id'}
        mock_boto3.client.return_value = mock_client

        recipients = ['recipient1@example.com', 'recipient2@example.com', 'recipient3@example.com']

        send_email_via_ses(
            smtp_from='sender@example.com',
            recipients=recipients,
            subject='Test Subject',
            body='Test body',
            access_key='AKIATEST123',
            secret_key='test-secret',
            session_token='test-token',
            region='us-east-1'
        )

        # Verify destinations include all recipients
        call_args = mock_client.send_raw_email.call_args[1]
        assert call_args['Destinations'] == recipients

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.ses_sender.boto3')
    def test_send_email_single_recipient_string(self, mock_boto3):
        """Test sending email to single recipient as string (not list)"""
        mock_client = mock.Mock()
        mock_client.send_raw_email.return_value = {'MessageId': 'test-message-id'}
        mock_boto3.client.return_value = mock_client

        send_email_via_ses(
            smtp_from='sender@example.com',
            recipients='recipient@example.com',  # String, not list
            subject='Test Subject',
            body='Test body',
            access_key='AKIATEST123',
            secret_key='test-secret',
            session_token='test-token',
            region='us-east-1'
        )

        # Should convert string to list
        call_args = mock_client.send_raw_email.call_args[1]
        assert call_args['Destinations'] == ['recipient@example.com']

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.ses_sender.boto3')
    def test_send_email_with_headers(self, mock_boto3):
        """Test sending email with custom headers"""
        mock_client = mock.Mock()
        mock_client.send_raw_email.return_value = {'MessageId': 'test-message-id'}
        mock_boto3.client.return_value = mock_client

        custom_headers = {
            'Reply-To': 'noreply@example.com',
            'X-Custom-Header': 'custom-value'
        }

        send_email_via_ses(
            smtp_from='sender@example.com',
            recipients=['recipient@example.com'],
            subject='Test Subject',
            body='Test body',
            headers=custom_headers,
            access_key='AKIATEST123',
            secret_key='test-secret',
            session_token='test-token',
            region='us-east-1'
        )

        # Verify headers are in the message
        call_args = mock_client.send_raw_email.call_args[1]
        raw_message = call_args['RawMessage']['Data']
        assert 'Reply-To: noreply@example.com' in raw_message
        assert 'X-Custom-Header: custom-value' in raw_message

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.ses_sender.boto3')
    def test_send_email_ses_error(self, mock_boto3):
        """Test handling of SES API errors"""
        from botocore.exceptions import ClientError

        mock_client = mock.Mock()
        mock_client.send_raw_email.side_effect = ClientError(
            {'Error': {'Code': 'MessageRejected', 'Message': 'Email address not verified'}},
            'SendRawEmail'
        )
        mock_boto3.client.return_value = mock_client

        with pytest.raises(Exception):
            send_email_via_ses(
                smtp_from='sender@example.com',
                recipients=['recipient@example.com'],
                subject='Test Subject',
                body='Test body',
                access_key='AKIATEST123',
                secret_key='test-secret',
                session_token='test-token',
                region='us-east-1'
            )

    @mock.patch('ckanext.hdx_smtp_assumerole.helpers.ses_sender.boto3')
    def test_send_email_with_mime_message(self, mock_boto3):
        """Test sending email with pre-built MIME message (including attachments)"""
        mock_client = mock.Mock()
        mock_client.send_raw_email.return_value = {'MessageId': 'test-message-id'}
        mock_boto3.client.return_value = mock_client

        # Build a MIME message with attachment (like hdx_users_mailer does)
        msg = MIMEMultipart()
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg['Subject'] = 'Test with Attachment'

        # Add HTML body
        body_html = '<html><body>Test email with attachment</body></html>'
        part = MIMEText(body_html, 'html', 'utf-8')
        msg.attach(part)

        # Add attachment
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(b'Test file content')
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', 'attachment; filename=test.txt')
        msg.attach(attachment)

        # Send with pre-built MIME message
        send_email_via_ses(
            smtp_from='sender@example.com',
            recipients=['recipient@example.com'],
            subject='Will be ignored',  # MIME message has its own subject
            mime_message=msg,
            access_key='AKIATEST123',
            secret_key='test-secret',
            session_token='test-token',
            region='us-east-1'
        )

        # Verify send_raw_email was called
        mock_client.send_raw_email.assert_called_once()
        call_args = mock_client.send_raw_email.call_args[1]

        # Verify the message contains attachment headers and structure
        raw_message = call_args['RawMessage']['Data']
        # Content is base64 encoded, so check for headers and MIME structure
        assert 'Content-Type: text/html' in raw_message
        assert 'Content-Disposition: attachment; filename=test.txt' in raw_message
        assert 'Content-Type: application/octet-stream' in raw_message
        assert 'Content-Transfer-Encoding: base64' in raw_message
