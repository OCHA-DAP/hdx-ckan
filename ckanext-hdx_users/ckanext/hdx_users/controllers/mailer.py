import logging
import smtplib
from email import Utils
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from time import time

import paste.deploy.converters
from pylons import config

import ckan
from ckan.common import _

log = logging.getLogger(__name__)

from ckan.lib.mailer import MailerException

# class MailerException(Exception):
#     pass


FOOTER = '''<br/><br/>
            <small>
            <p>
            <a href="https://data.humdata.org">Humanitarian Data Exchange</a> | 
            <a href="https://centre.humdata.org/">Centre for Humanitarian Data</a>
            </p>
            <p>
            <a href="https://u6071170.ct.sendgrid.net/wf/click?upn=ZHdJIgjLOeoTOGK6L-2F9eQfo8sxIRMpyyK32mFCoVDcw91sTCcAP5tzLa-2B9CJS9ZanybCKSQDXGUfoffLHuA9Zs5i4qpu5UFG7g59ZTIDzdjy3F5vT-2BfFXbcpThaQHIAQ_mbofbgt8Oy4XKscKiWkDyF5GtfwVPEWuKp1mp029nvP-2FI-2FaufXd94SDS9FWnD5fBl4Vol07EvZgBBz0KKIdejZDro0p4T5Bfo-2FDQ-2BQx8tiaKnn3-2BjTTRdJ4dGe3mFWDHPUwaqmD5ISHTUvzKfx3OiiliaS-2FObLVWOiQi-2F6J8ycsUI0rH9SI0if4SSswOtfrHnyFLwgeKhL4qMAW3tujfNpjK8uFFU-2Blgc6e8-2BlnGKh0-3D">Sign up for our newsletter</a> | 
            <a href="https://u6071170.ct.sendgrid.net/wf/click?upn=pSb122FWR4b4lo6A8X2F8mcY12WWW0EYb1kxpnksfa8JpvqR2sjRy5c6Ei5RPHzR_mbofbgt8Oy4XKscKiWkDyF5GtfwVPEWuKp1mp029nvP-2FI-2FaufXd94SDS9FWnD5fBl4Vol07EvZgBBz0KKIdejftt9iyMTZrmNGYdyEDpbCCSWhybEKt9wzgv5x-2BO7OJbQQfNtIUavmuTFmYsH6R-2FJz8BEMIwy4eXQUfjrq6NKTRw1dU1b6Go2pxxi7lNhglocHVuZc6MGG8wNhYt9BWK6erwwVwBjNoEKi4xBBpcwRA-3D">Follow us on Twitter</a> | 
            <a href="mailto:hdx@un.org" target="_top">Contact us</a>
            </p>
            </small>'''


def add_msg_niceties(body, footer=None):
    if not footer:
        footer = FOOTER
    style = u"""
      <style type="text/css">
        p {margin:0; padding:0; margin-bottom:0;}
      </style>
    """
    content = u'''
    {body}
    {footer}'''.format(body=body, footer=footer)

    full_html = u"""
    <html>
      <header>{style}</header>
      <body>
        <img style="max-width: 150px" src="https://data.humdata.org/images/homepage/logo-combined.png" />
        {content}
      </body>
    </html>
     """.format(style=style, content=content)
    return full_html


def _mail_recipient(recipients_list, subject, body, sender_name, bcc_recipients_list=None, footer=None, headers={},
                    sender_email=None, reply_wanted=False):
    mail_from = config.get('hdx_smtp.mail_from_please_reply') if reply_wanted else config.get('smtp.mail_from')
    body = add_msg_niceties(body=body, footer=footer)
    msg = MIMEMultipart('alternative')
    for k, v in headers.items(): msg[k] = v
    subject = Header(subject.encode('utf-8'), 'utf-8')
    msg['Subject'] = subject
    msg['From'] = _(u"%s <%s>") % (sender_name, mail_from)
    recipient_email_list = []
    recipient = u""
    if recipients_list:
        for r in recipients_list:
            email = r.get('email')
            recipient_email_list.append(email)
            display_name = r.get('display_name')
            if (display_name):
                recipient += u"%s <%s> , " % (display_name, email)
            else:
                recipient += u"%s , " % (email)
            # else:
            # no recipient list provided

    msg['To'] = Header(recipient, 'utf-8')
    if bcc_recipients_list:
        for r in bcc_recipients_list:
            recipient_email_list.append(r.get('email'))
    msg['Date'] = Utils.formatdate(time())
    msg['X-Mailer'] = "CKAN %s" % ckan.__version__
    if sender_email:
        msg['Reply-To'] = Header((u"%s <%s>" % (sender_name, sender_email)), 'utf-8')
    part = MIMEText(body, 'html', 'utf-8')
    msg.attach(part)

    # Send the email using Python's smtplib.
    smtp_connection = smtplib.SMTP()
    if 'smtp.test_server' in config:
        # If 'smtp.test_server' is configured we assume we're running tests,
        # and don't use the smtp.server, starttls, user, password etc. options.
        smtp_server = config['smtp.test_server']
        smtp_starttls = False
        smtp_user = None
        smtp_password = None
    else:
        smtp_server = config.get('smtp.server', 'localhost')
        smtp_starttls = paste.deploy.converters.asbool(
            config.get('smtp.starttls'))
        smtp_user = config.get('smtp.user')
        smtp_password = config.get('smtp.password')
    smtp_connection.connect(smtp_server)
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

    except smtplib.SMTPException, e:
        msg = '%r' % e
        log.exception(msg)
        raise MailerException(msg)
    finally:
        smtp_connection.quit()


def mail_recipient(recipients_list, subject, body, sender_name='HDX', sender_email=None, bcc_recipients_list=None,
                   footer=None, headers={}, reply_wanted=False):
    if recipients_list is None and bcc_recipients_list is None:
        raise MailerException('There are no recipients to send email')
    return _mail_recipient(recipients_list, subject, body, sender_name, bcc_recipients_list=bcc_recipients_list,
                           footer=footer, headers=headers, sender_email=sender_email, reply_wanted=reply_wanted)
