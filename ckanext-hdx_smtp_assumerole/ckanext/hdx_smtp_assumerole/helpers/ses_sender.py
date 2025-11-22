"""
SES API email sender - sends emails using boto3 SES API instead of SMTP.
This allows using temporary credentials with session tokens from AssumeRole.
"""
import logging
import boto3
from typing import Dict, List, Optional, Union, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger(__name__)


def send_email_via_ses(
    smtp_from: str,
    recipients: Union[str, List[str]],
    subject: str,
    body: Optional[str] = None,
    body_html: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    mime_message: Optional[Any] = None,
    access_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    session_token: Optional[str] = None,
    region: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send email using AWS SES API instead of SMTP.

    Args:
        smtp_from: Sender email address
        recipients: List of recipient email addresses (or single string)
        subject: Email subject
        body: Plain text body (can be None if body_html or mime_message is provided)
        body_html: HTML body (optional)
        headers: Additional email headers (dict)
        mime_message: Pre-built MIME message (email.mime object). If provided, body/body_html/subject/headers are ignored
        access_key: AWS access key ID
        secret_key: AWS secret access key
        session_token: AWS session token (for temporary credentials)
        region: AWS region

    Returns:
        dict: SES send_raw_email response

    Raises:
        Exception: If SES API call fails
    """
    if isinstance(recipients, str):
        recipients = [recipients]

    # Use pre-built MIME message if provided, otherwise build one
    if mime_message:
        msg = mime_message
    else:
        # Build MIME message
        if body_html:
            if body:
                # Both plain and HTML versions
                msg = MIMEMultipart('alternative')
                part1 = MIMEText(body, 'plain', 'utf-8')
                part2 = MIMEText(body_html, 'html', 'utf-8')
                msg.attach(part1)
                msg.attach(part2)
            else:
                # HTML only
                msg = MIMEMultipart()
                part = MIMEText(body_html, 'html', 'utf-8')
                msg.attach(part)
        else:
            # Plain text only
            msg = MIMEText(body, 'plain', 'utf-8')

        # Set standard headers (can be overridden by custom headers)
        msg['Subject'] = subject
        msg['From'] = smtp_from
        msg['To'] = ', '.join(recipients)

        # Add/override with custom headers
        if headers:
            for key, value in headers.items():
                # Skip empty headers and headers that are part of the message body
                if value and key not in ['Content-Type', 'MIME-Version', 'Content-Transfer-Encoding']:
                    # Replace existing header if it exists
                    if key in msg:
                        del msg[key]
                    msg[key] = value

    # Create SES client with temporary credentials
    ses_client = boto3.client(
        'ses',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name=region
    )

    try:
        response = ses_client.send_raw_email(
            Source=smtp_from,
            Destinations=recipients,
            RawMessage={'Data': msg.as_string()}
        )

        log.info(f'Email sent via SES API to {recipients}, MessageId: {response["MessageId"]}')
        return response

    except Exception as e:
        log.error(f'Failed to send email via SES API: {e}')
        raise
