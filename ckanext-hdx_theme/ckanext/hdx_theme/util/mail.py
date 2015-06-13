'''
Created on Jul 31, 2014

@author: alexandru-m-g
'''

import logging as logging
import exceptions as exceptions
import ckan.lib.mailer as mailer
import pylons.config as config

log = logging.getLogger(__name__)

def send_mail(recipients, subject, body):
    if recipients and len(recipients) > 0:
        email_info = u'\nSending email to {recipients} with subject "{subject}" with body: {body}'\
            .format(recipients=', '.join([r['display_name'] + ' - ' + r['email'] for r in recipients]), subject=subject, body=body)
        log.info(email_info)
        send_mails = config.get('hdx.orgrequest.sendmails', 'true')
        if 'true' == send_mails:
            for recipient in recipients:
                mailer.mail_recipient(recipient['display_name'], recipient['email'],
                    subject, body)
        else:
            log.warn('HDX-CKAN was configured to not send email requests')
    else:
        raise NoRecipientException('The are no recipients for this request. Contact an administrator ')


class NoRecipientException(exceptions.Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)
