import datetime
import logging

import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_org_group.helpers.analytics as org_analytics

log = logging.getLogger(__name__)
_check_access = tk.check_access
_get_or_bust = tk.get_or_bust
NotFound = tk.ObjectNotFound
get_action = tk.get_action
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


def hdx_send_request_data_auto_approval(context, data_dict):
    _check_access('hdx_send_request_data_auto_approval', context, {'package_id': data_dict.get('package_id')})

    model = context['model']

    req_dict = get_action('requestdata_request_show')(context, {'id': data_dict.get('id'),
                                                                'package_id': data_dict.get('package_id')})
    pkg_dict = get_action('package_show')(context, {'id': data_dict.get('package_id')})
    org_dict = get_action('organization_show')(context, {'id': pkg_dict.get('owner_org')})
    maintainer_obj = model.User.get(pkg_dict.get('maintainer'))

    subject = u'The metadata-only dataset you requested to access is now public: %s' % pkg_dict.get('name')

    email_data = {
        'user_fullname': req_dict.get('sender_name'),
        'org_name': org_dict.get('title'),
        'dataset_link': h.url_for('dataset_read', id=data_dict.get('package_id'), qualified=True),
        'dataset_title': pkg_dict.get('name')
    }
    hdx_mailer.mail_recipient([{'display_name': data_dict.get('requested_by'), 'email': req_dict.get('email_address')}],
                              subject, email_data, footer=data_dict.get('send_to'),
                              snippet='email/content/request_data_auto_approval_to_user.html')

    subject = u'%s’s request for access to one of your datasets: %s is archived' % (req_dict.get('sender_name'), pkg_dict.get('name'))

    email_data = {
        'user_fullname': req_dict.get('sender_name'),
        'user_email': req_dict.get('email_address'),
        'dataset_link': h.url_for('dataset_read', id=data_dict.get('package_id'), qualified=True),
        'dataset_title': pkg_dict.get('name')
    }
    hdx_mailer.mail_recipient([{'display_name': maintainer_obj.fullname, 'email': maintainer_obj.email}],
                              subject, email_data, footer=maintainer_obj.email,
                              snippet='email/content/request_data_auto_approval_to_admins.html')
