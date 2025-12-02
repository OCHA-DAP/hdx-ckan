# encoding: utf-8

import logging
import mimetypes
from typing import Dict, List, Optional, Tuple, Any, Union
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

import ckan.lib.mailer as mailer
from ckan import model
import ckan.plugins.toolkit as tk

from ckanext.hdx_smtp_assumerole.helpers.credentials_manager import SMTPCredentialsManager
from ckanext.hdx_smtp_assumerole.helpers.ses_sender import send_email_via_ses

log = logging.getLogger(__name__)

# Store original functions
_original_mail_user = None
_original_mail_recipient = None
_patches_applied = False


def _build_mime_message_with_attachments(
    mail_from: str,
    recipient_email: str,
    recipient_name: Optional[str],
    subject: str,
    body: str,
    body_html: Optional[str],
    headers: Optional[Dict[str, str]],
    attachments: Optional[List[Union[Tuple[str, Any], Tuple[str, Any, str]]]]
) -> MIMEMultipart:
    """
    Build a MIME message with optional HTML body and attachments.

    Shared logic for both mail_user and mail_recipient to avoid code duplication.

    :param mail_from: Sender email address
    :param recipient_email: Recipient email address
    :param recipient_name: Recipient display name (optional)
    :param subject: Email subject
    :param body: Plain text body
    :param body_html: HTML body (optional)
    :param headers: Additional headers dict (optional)
    :param attachments: List of attachment tuples (optional)
    :return: MIMEMultipart message object
    """
    msg = MIMEMultipart()
    msg['From'] = mail_from
    msg['Subject'] = subject

    # Add To header with display name
    if recipient_name:
        msg['To'] = f'"{recipient_name}" <{recipient_email}>'
    else:
        msg['To'] = recipient_email

    # Add custom headers
    if headers:
        for key, value in headers.items():
            if key not in ['From', 'To', 'Subject'] and value:
                msg[key] = value

    # Add body
    if body_html:
        if body:
            # Both plain and HTML
            msg_alt = MIMEMultipart('alternative')
            msg_alt.attach(MIMEText(body, 'plain', 'utf-8'))
            msg_alt.attach(MIMEText(body_html, 'html', 'utf-8'))
            msg.attach(msg_alt)
        else:
            # HTML only
            msg.attach(MIMEText(body_html, 'html', 'utf-8'))
    else:
        # Plain text only
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # Add attachments
    if attachments:
        for attachment in attachments:
            if len(attachment) == 3:
                filename, file_obj, media_type = attachment
            else:
                filename, file_obj = attachment
                media_type, _ = mimetypes.guess_type(filename)
                if not media_type:
                    media_type = 'application/octet-stream'

            maintype, subtype = media_type.split('/', 1)
            part = MIMEBase(maintype, subtype)
            part.set_payload(file_obj.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)

    return msg


def patch_mailer_functions() -> None:
    """
    Apply monkey patches to ckan.lib.mailer functions.
    Replaces SMTP-based email sending with SES API.

    This should be called once at application startup.
    Thread-safe - will only patch once even if called multiple times.
    """
    global _original_mail_user, _original_mail_recipient, _patches_applied

    if _patches_applied:
        log.debug('Mailer patches already applied, skipping')
        return

    log.debug('Applying monkey patches to ckan.lib.mailer to use SES API')

    # Store original functions
    _original_mail_user = mailer.mail_user
    _original_mail_recipient = mailer.mail_recipient

    # Apply patches to ckan.lib.mailer
    mailer.mail_user = patched_mail_user
    mailer.mail_recipient = patched_mail_recipient

    # Also patch ckan.plugins.toolkit to handle imports like tk.mail_recipient
    # This is needed for modules that import tk.mail_recipient before patches are applied
    try:
        import ckan.plugins.toolkit as tk
        tk.mail_user = patched_mail_user
        tk.mail_recipient = patched_mail_recipient
        log.debug('Successfully patched ckan.plugins.toolkit mail functions')
    except Exception as e:
        log.warning(f'Failed to patch ckan.plugins.toolkit: {e}')

    _patches_applied = True

    log.debug('Successfully patched ckan.lib.mailer to use SES API')


def patched_mail_user(
    recipient: Union[model.User, Dict[str, Any]],
    subject: str,
    body: str,
    body_html: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    attachments: Optional[List[Union[Tuple[str, Any], Tuple[str, Any, str]]]] = None
) -> None:
    """
    Patched version of ckan.lib.mailer.mail_user that uses SES API.

    :param recipient: User object or user dict
    :param subject: Email subject
    :param body: Email body (plain text)
    :param body_html: Email body (HTML)
    :param headers: Additional headers dict
    :param attachments: List of attachment tuples (filename, file_object) or (filename, file_object, media_type)
    :raises Exception: If SES credentials are not available or email sending fails
    """
    try:
        # Get credentials manager and ensure fresh credentials
        manager = SMTPCredentialsManager.get_instance()
        manager.ensure_fresh_credentials()

        # Get SES credentials
        ses_creds = manager.get_ses_credentials()
        if not ses_creds:
            error_msg = 'No SES credentials available - cannot send email'
            log.error(error_msg)
            raise Exception(error_msg)

        # Extract recipient email and name
        if isinstance(recipient, model.User):
            recipient_email = recipient.email
            recipient_name = recipient.display_name or recipient.name
        else:
            recipient_email = recipient.get('email')
            recipient_name = recipient.get('display_name') or recipient.get('name')

        # Get mail_from config
        config = tk.config
        mail_from = config.get('smtp.mail_from') or config.get('mail_from')

        # If we have attachments or body_html, build a complete MIME message
        if attachments or body_html:
            msg = _build_mime_message_with_attachments(
                mail_from, recipient_email, recipient_name, subject,
                body, body_html, headers, attachments
            )
            send_email_via_ses(
                smtp_from=mail_from,
                recipients=[recipient_email],
                subject=subject,
                mime_message=msg,
                access_key=ses_creds['access_key'],
                secret_key=ses_creds['secret_key'],
                session_token=ses_creds['session_token'],
                region=ses_creds['region']
            )
        else:
            # Simple plain text email - use simple mode
            if not headers:
                headers = {}
            if recipient_name:
                headers['To'] = f'"{recipient_name}" <{recipient_email}>'
            else:
                headers['To'] = recipient_email

            send_email_via_ses(
                smtp_from=mail_from,
                recipients=[recipient_email],
                subject=subject,
                body=body,
                headers=headers,
                access_key=ses_creds['access_key'],
                secret_key=ses_creds['secret_key'],
                session_token=ses_creds['session_token'],
                region=ses_creds['region']
            )

    except Exception as e:
        log.error(f'Failed to send email via SES API: {str(e)}')
        raise


def patched_mail_recipient(
    recipient_name: str,
    recipient_email: str,
    subject: str,
    body: str,
    body_html: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    attachments: Optional[List[Union[Tuple[str, Any], Tuple[str, Any, str]]]] = None
) -> None:
    """
    Patched version of ckan.lib.mailer.mail_recipient that uses SES API.

    :param recipient_name: Recipient name
    :param recipient_email: Recipient email address
    :param subject: Email subject
    :param body: Email body (plain text)
    :param body_html: Email body (HTML)
    :param headers: Additional headers dict
    :param attachments: List of attachment tuples (filename, file_object) or (filename, file_object, media_type)
    :raises Exception: If SES credentials are not available or email sending fails
    """
    try:
        # Get credentials manager and ensure fresh credentials
        manager = SMTPCredentialsManager.get_instance()
        manager.ensure_fresh_credentials()

        # Get SES credentials
        ses_creds = manager.get_ses_credentials()
        if not ses_creds:
            error_msg = 'No SES credentials available - cannot send email'
            log.error(error_msg)
            raise Exception(error_msg)

        # Get mail_from config
        config = tk.config
        mail_from = config.get('smtp.mail_from') or config.get('mail_from')

        # If we have attachments or body_html, build a complete MIME message
        if attachments or body_html:
            msg = _build_mime_message_with_attachments(
                mail_from, recipient_email, recipient_name, subject,
                body, body_html, headers, attachments
            )
            send_email_via_ses(
                smtp_from=mail_from,
                recipients=[recipient_email],
                subject=subject,
                mime_message=msg,
                access_key=ses_creds['access_key'],
                secret_key=ses_creds['secret_key'],
                session_token=ses_creds['session_token'],
                region=ses_creds['region']
            )
        else:
            # Simple plain text email - use simple mode
            send_email_via_ses(
                smtp_from=mail_from,
                recipients=[recipient_email],
                subject=subject,
                body=body,
                headers=headers,
                access_key=ses_creds['access_key'],
                secret_key=ses_creds['secret_key'],
                session_token=ses_creds['session_token'],
                region=ses_creds['region']
            )

    except Exception as e:
        log.error(f'Failed to send email via SES API: {str(e)}')
        raise


def unpatch_mailer_functions() -> None:
    """
    Remove monkey patches and restore original functions.
    Useful for testing or cleanup.
    """
    global _original_mail_user, _original_mail_recipient, _patches_applied

    if not _patches_applied:
        log.debug('Mailer patches not applied, nothing to unpatch')
        return

    log.info('Removing monkey patches from ckan.lib.mailer')

    # Restore original functions to ckan.lib.mailer
    if _original_mail_user is not None:
        mailer.mail_user = _original_mail_user
    if _original_mail_recipient is not None:
        mailer.mail_recipient = _original_mail_recipient

    # Also restore toolkit functions
    try:
        import ckan.plugins.toolkit as tk
        if _original_mail_user is not None:
            tk.mail_user = _original_mail_user
        if _original_mail_recipient is not None:
            tk.mail_recipient = _original_mail_recipient
        log.debug('Successfully restored ckan.plugins.toolkit mail functions')
    except Exception as e:
        log.warning(f'Failed to restore ckan.plugins.toolkit: {e}')

    _patches_applied = False

    log.info('Successfully removed patches from ckan.lib.mailer')


def is_patched() -> bool:
    """
    Check if mailer functions are currently patched.

    :return: True if patches are applied
    :rtype: bool
    """
    return _patches_applied
