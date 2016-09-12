'''
Created on Jul 31, 2014

@author: alexandru-m-g
'''

import logging as logging
import exceptions as exceptions
import ckan.lib.mailer as mailer
import pylons.config as config
import validate_email

import ckan.plugins.toolkit as tk
import ckanext.hdx_users.controllers.mailer as hdx_mailer

log = logging.getLogger(__name__)


def send_mail(recipients, subject, body, one_email=False):
    if recipients and len(recipients) > 0:
        email_info = u'\nSending email to {recipients} with subject "{subject}" with body: {body}' \
            .format(recipients=', '.join([r['display_name'] + ' - ' + r['email'] for r in recipients]), subject=subject,
                    body=body)
        log.info(email_info)
        send_mails = config.get('hdx.orgrequest.sendmails', 'true')
        if 'true' == send_mails:
            if one_email:
                new_recipients = []
                for recipient in recipients:
                    new_recipients.append({'name': recipient['display_name'], 'email': recipient['email']})
                    hdx_mailer.mail_recipient(recipient_name=None, recipient_email=None, subject=subject, body=body,
                                              recipients_list=new_recipients)
            else:
                for recipient in recipients:
                    hdx_mailer.mail_recipient(recipient['display_name'], recipient['email'], subject, body)
        else:
            log.warn('HDX-CKAN was configured to not send email requests')
    else:
        raise NoRecipientException('The are no recipients for this request. Contact an administrator ')


class NoRecipientException(exceptions.Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def simple_validate_email(email):
    '''
    Uses the validate_email library with check_mx=False, verify=False
    :param email: the email to validate
    :return: True if valid, raises Invalid exception otherwise
    '''
    if not validate_email.validate_email(email, check_mx=False, verify=False):
        raise tk.Invalid(tk._('Email address is not valid'))

    return True
