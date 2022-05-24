import cgi
import logging
import smtplib
import socket
import unicodedata
from email import encoders
from email import utils
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import time
from six import text_type, PY3

import ckan
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

from ckan.lib.mailer import MailerException
from ckan.lib.base import render_jinja2

config = tk.config
render = tk.render
_ = tk._
CHARSET = 'utf-8'


def mail_recipient(recipients_list, subject, body, sender_name='Humanitarian Data Exchange (HDX)',
                   sender_email='hdx@humdata.org', cc_recipients_list=None, bcc_recipients_list=None,
                   footer=None, headers={}, reply_wanted=False, snippet='email/email.html', file=None):
    if recipients_list is None and bcc_recipients_list is None:
        raise MailerException('There are no recipients to send email')
    return _mail_recipient_html(sender_name, sender_email, recipients_list, subject, content_dict=body,
                                cc_recipients_list=cc_recipients_list, bcc_recipients_list=bcc_recipients_list,
                                footer=footer, headers=headers, reply_wanted=reply_wanted, snippet=snippet, file=file)


def _mail_recipient_html(sender_name='Humanitarian Data Exchange (HDX)',
                         sender_email='hdx@humdata.org',
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
    # if sender_email:
    #     mail_from = sender_email
    # else:
    mail_from = config.get('smtp.mail_from')

    template_data = {
        'data': {
            'data': content_dict,
            'footer': footer,
            '_snippet': snippet,
            'logo_hdx_email': config.get('ckan.site_url', '#') + '/images/homepage/logo-hdx-email.png'
        },
    }
    # body_html = render_jinja2('email/email.html', template_data)
    body_html = render('email/email.html', template_data)

    # msg = MIMEMultipart('alternative')
    msg = MIMEMultipart()
    for k, v in headers.items(): msg[k] = v
    subject = Header(subject.encode(CHARSET), CHARSET)
    msg['Subject'] = subject
    msg['From'] = u'"{display_name}" <{email}>'.format(display_name='Humanitarian Data Exchange (HDX)', email=mail_from)
    recipient_email_list = []
    recipients = None
    if recipients_list:
        for r in recipients_list:
            email = r.get('email')
            recipient_email_list.append(email)
            display_name = r.get('display_name')
            if display_name:
                recipient = u'"{display_name}" <{email}>'.format(display_name=_get_decoded_str(display_name),
                                                                 email=email)
                # recipient = _get_decoded_address(display_name, email)
            else:
                recipient = u'{email}'.format(email=email)
            # else:
            # no recipient list provided
            recipients = u', '.join([recipients, recipient]) if recipients else recipient

    msg['To'] = recipients if PY3 else Header(recipients, CHARSET)

    if bcc_recipients_list:
        for r in bcc_recipients_list:
            recipient_email_list.append(r.get('email'))
    cc_recipients = None
    if cc_recipients_list:
        for r in cc_recipients_list:
            recipient_email_list.append(r.get('email'))
            cc_recipient = u'"{display_name}" <{email}>'.format(display_name=_get_decoded_str(r.get('display_name')),
                                                                email=r.get('email'))
            cc_recipients = u', '.join([cc_recipients, cc_recipient]) if cc_recipients else cc_recipient
        if cc_recipients:
            msg['Cc'] = cc_recipients if PY3 else Header(cc_recipients, CHARSET)
        else:
            msg['Cc'] = ''

    msg['Date'] = utils.formatdate(time())
    msg['X-Mailer'] = "CKAN %s" % ckan.__version__
    # if sender_email:
    reply_to = u'"{display_name}" <{email}>'.format(display_name=_get_decoded_str(sender_name), email=sender_email)
    msg['Reply-To'] = reply_to if PY3 else Header(reply_to, CHARSET)
    part = MIMEText(body_html, 'html', CHARSET)
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


def _get_decoded_str(display_name):
    if display_name:
        try:
            # encoded_display_name = display_name.encode(CHARSET)
            decoded_display_name = unicodedata.normalize(u'NFKD', text_type(display_name)).encode('ascii', 'ignore').decode('utf8')
            return decoded_display_name
        except Exception as ex:
            log.error(ex)
    return display_name
#
#
# def _get_decoded_address(display_name, email):
#     return utils.formataddr((display_name, email)).encode('utf-8')
