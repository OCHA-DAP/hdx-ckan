# encoding: utf-8

import logging
import cgi

from typing import Dict, List, Optional, Tuple, Any
from email import utils
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import time
from six import PY3
from email import encoders

import ckan
import ckan.plugins.toolkit as tk

from ckanext.hdx_smtp_assumerole.helpers.caching import get_ses_credentials
from ckanext.hdx_smtp_assumerole.helpers.ses_sender import send_email_via_ses

log = logging.getLogger(__name__)

# Store original function
_original_mail_recipient_html = None
_patches_applied = False

CHARSET = 'utf-8'


def patch_hdx_users_mailer() -> None:
    """
    Apply monkey patches to ckanext.hdx_users.helpers.mailer.
    Replaces SMTP-based email sending with SES API.

    This should be called once at application startup.
    Thread-safe - will only patch once even if called multiple times.
    """
    global _original_mail_recipient_html, _patches_applied

    if _patches_applied:
        log.debug('HDX users mailer patches already applied, skipping')
        return

    try:
        # Import hdx_users mailer module
        from ckanext.hdx_users.helpers import mailer as hdx_mailer

        log.debug('Applying monkey patches to ckanext.hdx_users.helpers.mailer to use SES API')

        # Store original function
        _original_mail_recipient_html = hdx_mailer._mail_recipient_html

        # Apply patch
        hdx_mailer._mail_recipient_html = patched_mail_recipient_html

        _patches_applied = True

        log.debug('Successfully patched ckanext.hdx_users.helpers.mailer to use SES API')

    except ImportError:
        log.warning('ckanext.hdx_users not found, skipping HDX users mailer patches')
    except Exception as e:
        log.error(f'Error patching HDX users mailer: {str(e)}')


def patched_mail_recipient_html(
    sender_name: str = 'Humanitarian Data Exchange (HDX)',
    sender_email: str = 'hdx@humdata.org',
    recipients_list: Optional[List[Dict[str, str]]] = None,
    subject: Optional[str] = None,
    content_dict: Optional[Dict[str, Any]] = None,
    cc_recipients_list: Optional[List[Dict[str, str]]] = None,
    bcc_recipients_list: Optional[List[Dict[str, str]]] = None,
    footer: bool = True,
    headers: Dict[str, str] = {},
    reply_wanted: bool = False,
    snippet: str = 'email/email.html',
    file: Optional[Tuple[str, Any]] = None
) -> None:
    """
    Patched version of hdx_users._mail_recipient_html that uses SES API.

    :raises Exception: If SES credentials are not available or email sending fails
    """
    try:
        # Get SES credentials (dogpile cache handles credential refresh automatically)
        # Raises SESAssumeRoleException if credentials cannot be loaded
        ses_creds = get_ses_credentials()

        # Build email message (similar to original code)
        config = tk.config
        mail_from = config.get('smtp.mail_from')

        template_data = {
            'data': {
                'data': content_dict,
                'footer': footer,
                '_snippet': snippet,
                'logo_hdx_email': config.get('ckan.site_url', '#') + '/images/homepage/logo-hdx.png'
            },
        }
        body_html = tk.render('email/email.html', template_data)

        # Build MIME message
        msg = MIMEMultipart()
        for k, v in headers.items():
            msg[k] = v

        subject_header = Header(subject.encode(CHARSET), CHARSET)
        msg['Subject'] = subject_header
        msg['From'] = f'"{sender_name}" <{mail_from}>'

        recipient_email_list = []
        recipients = None

        if recipients_list:
            for r in recipients_list:
                email = r.get('email')
                recipient_email_list.append(email)
                display_name = r.get('display_name')
                if display_name:
                    decoded_name = _get_decoded_str(display_name)
                    recipient = f'"{decoded_name}" <{email}>'
                else:
                    recipient = email
                recipients = u', '.join([recipients, recipient]) if recipients else recipient

        msg['To'] = recipients if PY3 else Header(recipients, CHARSET)

        if bcc_recipients_list:
            for r in bcc_recipients_list:
                recipient_email_list.append(r.get('email'))

        cc_recipients = None
        if cc_recipients_list:
            for r in cc_recipients_list:
                recipient_email_list.append(r.get('email'))
                cc_display_name = _get_decoded_str(r.get('display_name'))
                cc_email = r.get('email')
                cc_recipient = f'"{cc_display_name}" <{cc_email}>'
                cc_recipients = u', '.join([cc_recipients, cc_recipient]) if cc_recipients else cc_recipient
            if cc_recipients:
                msg['Cc'] = cc_recipients if PY3 else Header(cc_recipients, CHARSET)
            else:
                msg['Cc'] = ''

        msg['Date'] = utils.formatdate(time())
        msg['X-Mailer'] = "CKAN %s" % ckan.__version__

        reply_to_name = _get_decoded_str(sender_name)
        reply_to = f'"{reply_to_name}" <{sender_email}>'
        msg['Reply-To'] = reply_to if PY3 else Header(reply_to, CHARSET)

        part = MIMEText(body_html, 'html', CHARSET)
        msg.attach(part)

        if isinstance(file, cgi.FieldStorage):
            _part = MIMEBase('application', 'octet-stream')
            _part.set_payload(file.file.read())
            encoders.encode_base64(_part)
            extension = file.filename.split('.')[-1]
            header_value = f'attachment; filename=attachment.{extension}'
            _part.add_header('Content-Disposition', header_value)
            msg.attach(_part)

        # Send via SES API with pre-built MIME message (includes attachments)
        send_email_via_ses(
            smtp_from=mail_from,
            recipients=recipient_email_list,
            subject=subject,
            mime_message=msg,  # Pass complete MIME message with attachments
            access_key=ses_creds['access_key'],
            secret_key=ses_creds['secret_key'],
            session_token=ses_creds['session_token'],
            region=ses_creds['region']
        )

    except Exception as e:
        log.error(f'Failed to send email via SES API: {str(e)}')
        raise


def _get_decoded_str(display_name: Optional[str]) -> str:
    """Helper function to decode display names (copied from hdx_users mailer)."""
    if display_name:
        try:
            decoded = ''
            for text, charset in Header(display_name).decode_header():
                if charset:
                    decoded += text.decode(charset)
                elif isinstance(text, bytes):
                    decoded += text.decode('utf-8')
                else:
                    decoded += text
            return decoded
        except Exception as e:
            log.warning(f'Error decoding display name: {e}')
            return display_name
    return ''


def unpatch_hdx_users_mailer() -> None:
    """
    Remove monkey patches and restore original functions.
    Useful for testing or cleanup.
    """
    global _original_mail_recipient_html, _patches_applied

    if not _patches_applied:
        log.debug('HDX users mailer patches not applied, nothing to unpatch')
        return

    try:
        from ckanext.hdx_users.helpers import mailer as hdx_mailer

        log.info('Removing monkey patches from ckanext.hdx_users.helpers.mailer')

        # Restore original function
        if _original_mail_recipient_html is not None:
            hdx_mailer._mail_recipient_html = _original_mail_recipient_html

        _patches_applied = False

        log.info('Successfully removed patches from ckanext.hdx_users.helpers.mailer')

    except ImportError:
        log.warning('ckanext.hdx_users not found during unpatch')
    except Exception as e:
        log.error(f'Error unpatching HDX users mailer: {str(e)}')


def is_patched() -> bool:
    """
    Check if hdx_users mailer is currently patched.

    :return: True if patches are applied
    :rtype: bool
    """
    return _patches_applied
