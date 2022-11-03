import datetime
import logging

import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_org_group.helpers.analytics as org_analytics

log = logging.getLogger(__name__)
_check_access = tk.check_access
_get_or_bust = tk.get_or_bust
NotFound = tk.ObjectNotFound
config = tk.config
g = tk.g
_ = tk._


def hdx_send_new_org_request(context, data_dict):
    _check_access('hdx_send_new_org_request', context, data_dict)

    email = config.get('hdx.orgrequest.email', None)
    if not email:
        email = 'hdx@un.org'
    display_name = 'HDX Feedback'

    ckan_username = g.user
    ckan_email = ''
    if g.userobj:
        ckan_email = g.userobj.email
    if config.get('hdx.onboarding.send_confirmation_email', 'false') == 'true':
        hdx_email = config.get('hdx.faqrequest.email', 'hdx@humdata.org')
        subject = u'Request to create a new organisation on HDX'
        email_data = {
            'org_name': data_dict.get('name', ''),
            'org_acronym': data_dict.get('acronym', ''),
            'org_description': data_dict.get('description', ''),
            'org_type': data_dict.get('org_type', ''),
            'org_website': data_dict.get('org_url', ''),
            'data_description': data_dict.get('description_data', ''),
            'requestor_work_email': data_dict.get('work_email', ''),
            'requestor_hdx_username': ckan_username,
            'requestor_hdx_email': ckan_email,
            'request_time': datetime.datetime.now().isoformat(),
            'user_fullname': data_dict.get('your_name', ''),
        }
        hdx_mailer.mail_recipient([{'display_name': 'Humanitarian Data Exchange (HDX)', 'email': hdx_email}],
                                  subject, email_data, sender_name=data_dict.get('your_name', ''),
                                  sender_email=ckan_email,
                                  snippet='email/content/new_org_request_hdx_team_notification.html')

        subject = u'Confirmation of your request to create a new organisation on HDX'
        email_data = {
            'org_name': data_dict.get('name', ''),
            'user_fullname': data_dict.get('your_name', ''),
        }
        hdx_mailer.mail_recipient([{'display_name': data_dict.get('your_name', ''), 'email': ckan_email}],
                                  subject, email_data, footer=ckan_email,
                                  snippet='email/content/new_org_request_confirmation_to_user.html')

        org_analytics.OrganizationRequestAnalyticsSender(data_dict.get('name', ''), data_dict.get('org_type', '')) \
            .send_to_queue()
