import smtplib
import socket
import logging
import cgi
from email import utils
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import time
from email.mime.base import MIMEBase
from email import encoders

from pylons import config

import ckan
from ckan.common import _

log = logging.getLogger(__name__)

from ckan.lib.mailer import MailerException
from ckan.lib.base import render_jinja2


def mail_recipient(recipients_list, subject, body, sender_name='Humanitarian Data Exchange (HDX)',
                   sender_email='hdx@un.org', cc_recipients_list=None, bcc_recipients_list=None,
                   footer=None, headers={}, reply_wanted=False, snippet='email/email.html', file=None):
    if recipients_list is None and bcc_recipients_list is None:
        raise MailerException('There are no recipients to send email')
    return _mail_recipient_html(sender_name, sender_email, recipients_list, subject, content_dict=body,
                                cc_recipients_list=cc_recipients_list, bcc_recipients_list=bcc_recipients_list,
                                footer=footer, headers=headers, reply_wanted=reply_wanted, snippet=snippet, file=file)


def _mail_recipient_html(sender_name='Humanitarian Data Exchange (HDX)',
                         sender_email='hdx@un.org',
                         recipients_list=None,
                         subject=None,
                         content_dict=None,
                         cc_recipients_list=None,
                         bcc_recipients_list=None,
                         footer=True,
                         headers={},
                         reply_wanted=False,
                         snippet='email/email.html',
                         file=None):
    if sender_email:
        mail_from = sender_email
    else:
        mail_from = config.get('hdx_smtp.mail_from_please_reply') if reply_wanted else config.get('smtp.mail_from')

    template_data = {
        'data': {
            'data': content_dict,
            'footer': footer,
            '_snippet': snippet
        },
    }
    body_html = render_jinja2('email/email.html', template_data)

    # msg = MIMEMultipart('alternative')
    msg = MIMEMultipart()
    for k, v in headers.items(): msg[k] = v
    subject = Header(subject.encode('utf-8'), 'utf-8')
    msg['Subject'] = subject
    msg['From'] = _(u"%s <%s>") % (sender_name, mail_from)
    recipient_email_list = []
    recipients = None
    if recipients_list:
        for r in recipients_list:
            email = r.get('email')
            recipient_email_list.append(email)
            display_name = r.get('display_name')
            if display_name:
                recipient = u"%s <%s>" % (display_name, email)
            else:
                recipient = u"%s" % email
            # else:
            # no recipient list provided
            recipients = ', '.join([recipients, recipient]) if recipients else recipient

    msg['To'] = Header(recipients, 'utf-8')
    if bcc_recipients_list:
        for r in bcc_recipients_list:
            recipient_email_list.append(r.get('email'))
    cc_recipients = None
    if cc_recipients_list:
        for r in cc_recipients_list:
            recipient_email_list.append(r.get('email'))
            cc_recipient = u"%s <%s>" % (r.get('display_name'), r.get('email'))
            cc_recipients = ', '.join([cc_recipients, cc_recipient]) if cc_recipients else cc_recipient
        msg['Cc'] = cc_recipients if cc_recipients else ''

    msg['Date'] = utils.formatdate(time())
    msg['X-Mailer'] = "CKAN %s" % ckan.__version__
    if sender_email:
        msg['Reply-To'] = Header((u"%s <%s>" % (sender_name, sender_email)), 'utf-8')
    part = MIMEText(body_html, 'html', 'utf-8')
    msg.attach(part)

    if isinstance(file, cgi.FieldStorage):
        _part = MIMEBase('application', 'octet-stream')
        _part.set_payload(file.file.read())
        encoders.encode_base64(_part)
        extension = file.filename.split('.')[-1]
        header_value = 'attachment; filename=attachment.{0}'.format(extension)
        _part.add_header('Content-Disposition', header_value)
        msg.attach(_part)

    # Send the email using Python's smtplib.
    # smtp_connection = smtplib.SMTP()
    if 'smtp.test_server' in config:
        # If 'smtp.test_server' is configured we assume we're running tests,
        # and don't use the smtp.server, starttls, user, password etc. options.
        smtp_server = config['smtp.test_server']
        smtp_starttls = False
        smtp_user = None
        smtp_password = None
    else:
        smtp_server = config.get('smtp.server', 'localhost')
        smtp_starttls = ckan.common.asbool(
            config.get('smtp.starttls'))
        smtp_user = config.get('smtp.user')
        smtp_password = config.get('smtp.password')
    # smtp_connection.connect(smtp_server)
    try:
        smtp_connection = smtplib.SMTP(smtp_server)
    except (socket.error, smtplib.SMTPConnectError) as e:
        log.exception(e)
        raise MailerException('SMTP server could not be connected to: "%s" %s'
                              % (smtp_server, e))
    try:
        # smtp_connection.set_debuglevel(True)

        # Identify ourselves and prompt the server for supported features.
        smtp_connection.ehlo()

        # If 'smtp.starttls' is on in CKAN config, try to put the SMTP
        # connection into TLS mode.
        if smtp_starttls:
            if smtp_connection.has_extn('STARTTLS'):
                smtp_connection.starttls()
                # Re-identify ourselves over TLS connection.
                smtp_connection.ehlo()
            else:
                raise MailerException("SMTP server does not support STARTTLS")

        # If 'smtp.user' is in CKAN config, try to login to SMTP server.
        if smtp_user:
            assert smtp_password, ("If smtp.user is configured then "
                                   "smtp.password must be configured as well.")
            smtp_connection.login(smtp_user, smtp_password)

        smtp_connection.sendmail(mail_from, recipient_email_list, msg.as_string())
        log.info("Sent email to provided list of recipients")

    except smtplib.SMTPException as e:
        msg = '%r' % e
        log.exception(msg)
        raise MailerException(msg)
    finally:
        smtp_connection.quit()
