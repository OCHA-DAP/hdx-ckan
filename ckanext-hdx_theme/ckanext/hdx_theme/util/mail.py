'''
Created on Jul 31, 2014

@author: alexandru-m-g
'''

import logging as logging

import ckanext.hdx_users.helpers.mailer as hdx_mailer

import ckan.plugins.toolkit as tk

get_validator = tk.get_validator
config = tk.config
log = logging.getLogger(__name__)


def send_mail(rawRecipients, subject, body, one_email=False):
    if rawRecipients and len(rawRecipients) > 0:
        recipients = [] # cleaned list
        for recipient in rawRecipients:
            if 'email' in recipient and 'display_name' in recipient and recipient['email'] is not None and recipient['display_name'] is not None:
                recipients.append(recipient)

        email_info = u'\nSending email to {recipients} with subject "{subject}" with body: {body}' \
            .format(recipients=', '.join([r['display_name'] + ' - ' + r['email'] for r in recipients]), subject=subject,
                    body=body)
        log.info(email_info)
        send_mails = config.get('hdx.orgrequest.sendmails', 'true')
        if 'true' == send_mails:
            if one_email:
                # new_recipients = []
                # for recipient in recipients:
                #     new_recipients.append({'name': recipient['display_name'], 'email': recipient['email']})
                hdx_mailer.mail_recipient(recipients_list=recipients, subject=subject, body=body)
            else:
                for recipient in recipients:
                    hdx_mailer.mail_recipient([recipient], subject, body)
        else:
            log.warn('HDX-CKAN was configured to not send email requests')
    else:
        raise NoRecipientException('The are no recipients for this request. Contact an administrator ')


class NoRecipientException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def hdx_validate_email(email):
    '''
    Wrapper for email_validator from ckan core
    :param email: the email to validate
    :return: True if valid, raises Invalid exception otherwise
    '''

    v = get_validator('email_validator')(email, {})

    return True
