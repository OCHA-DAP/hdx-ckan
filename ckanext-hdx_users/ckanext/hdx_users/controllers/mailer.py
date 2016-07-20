import smtplib
import logging
from time import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email import Utils

from pylons import config
import paste.deploy.converters

import ckan

from ckan.common import _, g

log = logging.getLogger(__name__)


class MailerException(Exception):
    pass


def add_msg_niceties(recipient_name, body, sender_name=None, sender_url=None, footer=None, show_header=True):
    if not footer:
        footer = '<br><br><small><p><a href="https://data.humdata.org">Humanitarian Data Exchange</a></p>' + '<p>Sign up for <a href="http://eepurl.com/PlJgH">Blogs</a> | <a href="https://twitter.com/humdata">Follow us on Twitter</a> | <a href="mailto:hdx@un.org" target="_top">Contact us</a></p></small>'
    if show_header:
        header = '''Dear {recipient_name},'''.format(recipient_name=recipient_name)
    else:
        header = ''
    content = '''{header}
    {body}
    {footer}'''.format(header=header, body=body, footer=footer)

    full_html = """
    <html>
      <header></header>
      <body>{content}</body>
    </html>
     """.format(content=content)
    return full_html


def _mail_recipient(recipient_name, recipient_email, sender_name, sender_url, subject, body, headers={},
                    recipients_list=None, footer=None, show_header=True, sender_email=None, bcc_recipients_list=None):
    mail_from = config.get('smtp.mail_from')
    body = add_msg_niceties(recipient_name=recipient_name, body=body, sender_name=sender_name, sender_url=sender_url,
                            footer=footer, show_header=show_header)
    msg = MIMEMultipart('alternative')
    for k, v in headers.items(): msg[k] = v
    subject = Header(subject.encode('utf-8'), 'utf-8')
    msg['Subject'] = subject
    msg['From'] = _("%s <%s>") % (sender_name, mail_from)
    recipient_email_list = []
    recipient = u""
    if recipients_list:
        for r in recipients_list:
            recipient_email_list.append(r.get('email'))
            recipient += u"%s <%s> , " % (r.get('name'), r.get('email'))
    else:
        recipient = u"%s <%s>, " % (recipient_name, recipient_email)
        recipient_email_list = [recipient_email]
    msg['To'] = Header(recipient, 'utf-8')
    # bcc_recipient = ''
    if bcc_recipients_list:
        for r in bcc_recipients_list:
            recipient_email_list.append(r.get('email'))
            # bcc_recipient += u"%s <%s> , " % (r.get('name'), r.get('email'))
        # msg['Bcc'] = Header(bcc_recipient, 'utf-8')
    msg['Date'] = Utils.formatdate(time())
    msg['X-Mailer'] = "CKAN %s" % ckan.__version__
    if sender_email:
        msg['Reply-To'] = Header((u"%s <%s>" % (sender_name, sender_email)), 'utf-8')
    part = MIMEText(body, 'html')
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
        log.info("Sent email to {0}".format(recipient_email))

    except smtplib.SMTPException, e:
        msg = '%r' % e
        log.exception(msg)
        raise MailerException(msg)
    finally:
        smtp_connection.quit()


def mail_recipient(recipient_name, recipient_email, subject, body, headers={}, recipients_list=None, footer=None,
                   sender_name='HDX', sender_email=None, bcc_recipients_list=None):
    return _mail_recipient(recipient_name=recipient_name, recipient_email=recipient_email, sender_name=sender_name,
                           sender_url=g.site_url, subject=subject, body=body, headers=headers,
                           recipients_list=recipients_list, footer=footer, show_header=False, sender_email=sender_email,
                           bcc_recipients_list=bcc_recipients_list)
