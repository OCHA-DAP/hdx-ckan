import datetime
import logging

import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_org_group.helpers.analytics as org_analytics
import ckan.model as model

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
    user_obj = model.User.get(ckan_username)
    if user_obj:
        user_fullname = user_obj.fullname or user_obj.display_name
    else:
        user_fullname = 'User'
    if config.get('hdx.onboarding.send_confirmation_email'):
        hdx_email = config.get('hdx.faqrequest.email')
        email_data = {
            'org_name': data_dict.get('name', ''),
            'org_description': data_dict.get('description', ''),
            'org_website': data_dict.get('website', ''),
            'data_type': data_dict.get('data_type', ''),
            'data_already_available': data_dict.get('data_already_available', ''),
            'data_already_available_link': data_dict.get('data_already_available_link', ''),
            'user_fullname': user_fullname,
            'requestor_hdx_username': ckan_username,
            'user_role': data_dict.get('role', ''),
            'requestor_hdx_email': ckan_email,
            'request_time': datetime.datetime.now().isoformat(),
        }
        subject = u'Request to create a new organisation on HDX'
        hdx_mailer.mail_recipient([{'display_name': 'Humanitarian Data Exchange (HDX)', 'email': hdx_email}],
                                  subject, email_data, sender_name=user_fullname,
                                  sender_email=ckan_email,
                                  snippet='email/content/new_org_request_hdx_team_notification.html')

        subject = u'Thank you for your request to create an organisation on HDX'
        email_data = {
            'user_fullname': user_fullname,
        }
        hdx_mailer.mail_recipient([{'display_name': user_fullname, 'email': ckan_email}],
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
