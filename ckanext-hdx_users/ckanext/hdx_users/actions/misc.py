import logging
import ckan.plugins.toolkit as tk
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.logic as logic
import pylons.configuration as configuration
import ckanext.hdx_theme.util.mail as hdx_mail
import ckanext.hdx_users.controllers.mailer as hdx_mailer
import datetime

from pylons import config
from ckan.common import c, _

log = logging.getLogger(__name__)
_check_access = tk.check_access
_get_or_bust = tk.get_or_bust
NotFound = logic.NotFound


def hdx_send_new_org_request(context, data_dict):
    _check_access('hdx_send_new_org_request', context, data_dict)

    email = config.get('hdx.orgrequest.email', None)
    if not email:
        email = 'hdx@un.org'
    display_name = 'HDX Feedback'

    ckan_username = c.user
    ckan_email = ''
    if c.userobj:
        ckan_email = c.userobj.email
    if configuration.config.get('hdx.onboarding.send_confirmation_email', 'false') == 'true':

        # body = _('<h3>New organisation request </h3><br/>' \
        #          'Organisation Name: {org_name}<br/>' \
        #          'Organisation Description: {org_description}<br/>' \
        #          'Organisation Data Description: {org_description_data}<br/>' \
        #          'Work email: {org_work_email}<br/>' \
        #          'Organisation URL: {org_url}<br/>' \
        #          'Organisation Type: {hdx_org_type}<br/>' \
        #          'Organisation Acronym: {org_acronym}<br/>' \
        #          'Person requesting: {person_name}<br/>' \
        #          'Person\'s email: {person_email}<br/>' \
        #          'Person\'s ckan username: {ckan_username}<br/>' \
        #          'Person\'s ckan email: {ckan_email}<br/>' \
        #          'Request time: {request_time}<br/>' \
        #          '(This is an automated mail)<br/><br/>' \
        #          '').format(org_name=data_dict.get('name',''), org_description=data_dict.get('description',''),
        #                     org_description_data=data_dict.get('description_data',''),
        #                     org_work_email=data_dict.get('work_email', ''),
        #                     org_url=data_dict.get('org_url',''), org_acronym=data_dict.get('acronym',''),
        #                     hdx_org_type=data_dict.get('org_type',''),
        #                     person_name=data_dict.get('your_name',''),
        #                     person_email=data_dict.get('your_email',''),
        #                     ckan_username=ckan_username, ckan_email=ckan_email,
        #                     request_time=datetime.datetime.now().isoformat())
        hdx_email = configuration.config.get('hdx.faqrequest.email', 'hdx@un.org')
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
            # 'org_acronym': data_dict.get('acronym', ''),
            # 'org_description': data_dict.get('description', ''),
            # 'org_type': data_dict.get('org_type', ''),
            # 'org_website': data_dict.get('org_url', ''),
            # 'data_description': data_dict.get('description_data', ''),
            # 'requestor_work_email': data_dict.get('work_email', ''),
            # 'requestor_hdx_username': ckan_username,
            # 'requestor_hdx_email': ckan_email,
            # 'request_time': datetime.datetime.now().isoformat(),
            'user_fullname': data_dict.get('your_name', ''),
        }
        hdx_mailer.mail_recipient([{'display_name': data_dict.get('your_name', ''), 'email': ckan_email}],
                                  subject, email_data, footer=ckan_email,
                                  snippet='email/content/new_org_request_confirmation_to_user.html')

# replaced with hdx_user_show from actions.py from hdx_theme
# def hdx_user_show(context, data_dict):
#     '''Return a user account.
#
#     Either the ``id`` or the ``user_obj`` parameter must be given.
#
#     :param id: the id or name of the user (optional)
#     :type id: string
#     :param user_obj: the user dictionary of the user (optional)
#     :type user_obj: user dictionary
#     :param include_datasets: Include a list of datasets the user has created.
#         If it is the same user or a sysadmin requesting, it includes datasets
#         that are draft or private.
#         (optional, default:``False``, limit:50)
#     :type include_datasets: boolean
#     :param include_num_followers: Include the number of followers the user has
#          (optional, default:``False``)
#     :type include_num_followers: boolean
#
#     :returns: the details of the user. Includes email_hash, number_of_edits and
#         number_created_packages (which excludes draft or private datasets
#         unless it is the same user or sysadmin making the request). Excludes
#         the password (hash) and reset_key. If it is the same user or a
#         sysadmin requesting, the email and apikey are included.
#     :rtype: dictionary
#
#     '''
#     model = context['model']
#
#     id = data_dict.get('id', None)
#     provided_user = data_dict.get('user_obj', None)
#     if id:
#         user_obj = model.User.get(id)
#         context['user_obj'] = user_obj
#         if user_obj is None:
#             raise NotFound
#     elif provided_user:
#         context['user_obj'] = user_obj = provided_user
#     else:
#         raise NotFound
#
#     _check_access('user_show', context, data_dict)
#
#     user_dict = model_dictize.user_dictize(user_obj, context)
#
#     # include private and draft datasets?
#     requester = context.get('user')
#     if requester:
#         requester_looking_at_own_account = requester == user_obj.name
#         include_private_and_draft_datasets = \
#             new_authz.is_sysadmin(requester) or \
#             requester_looking_at_own_account
#     else:
#         include_private_and_draft_datasets = False
#     context['count_private_and_draft_datasets'] = \
#         include_private_and_draft_datasets
#
#     user_dict = model_dictize.user_dictize(user_obj, context)
#
#     if context.get('return_minimal'):
#         log.warning('Use of the "return_minimal" in user_show is '
#                     'deprecated.')
#         return user_dict
#
#     if data_dict.get('include_datasets', False):
#         offset = data_dict.get('offset', 0)
#         limit = data_dict.get('limit', 20)
#         user_dict['datasets'] = []
#
#         dataset_q = model.Session.query(model.Package).join(model.PackageRole).filter_by(user=user_obj, role=model.Role.ADMIN).offset(offset).limit(limit)
#
#         if not include_private_and_draft_datasets:
#             dataset_q = dataset_q \
#                 .filter_by(state='active') \
#                 .filter_by(private=False)
#         else:
#             dataset_q = dataset_q \
#                 .filter(model.Package.state != 'deleted')
#
#         dataset_q_counter = model.Session.query(model.Package).join(model.PackageRole).filter_by(user=user_obj, role=model.Role.ADMIN).count()
#
#         for dataset in dataset_q:
#             try:
#                 dataset_dict = logic.get_action('package_show')(
#                     context, {'id': dataset.id})
#                 del context['package']
#             except logic.NotAuthorized:
#                 continue
#             user_dict['datasets'].append(dataset_dict)
#
#     revisions_q = model.Session.query(model.Revision
#                                       ).filter_by(author=user_obj.name)
#
#     revisions_list = []
#     for revision in revisions_q.limit(20).all():
#         revision_dict = tk.get_action('revision_show')(context, {'id': revision.id})
#         revision_dict['state'] = revision.state
#         revisions_list.append(revision_dict)
#     user_dict['activity'] = revisions_list
#
#     user_dict['num_followers'] = tk.get_action('user_follower_count')(
#         {'model': model, 'session': model.Session},
#         {'id': user_dict['id']})
#     user_dict['total_count'] = dataset_q_counter
#     return user_dict


# moved to get.py
# def hdx_user_show(context, data_dict):
#     '''Return a user account.
#
#     Either the ``id`` or the ``user_obj`` parameter must be given.
#
#     :param id: the id or name of the user (optional)
#     :type id: string
#     :param user_obj: the user dictionary of the user (optional)
#     :type user_obj: user dictionary
#
#     :rtype: dictionary
#
#     '''
#     model = context['model']
#
#     id = data_dict.get('id', None)
#     provided_user = data_dict.get('user_obj', None)
#     if id:
#         user_obj = model.User.get(id)
#         context['user_obj'] = user_obj
#         if user_obj is None:
#             raise logic.NotFound
#     elif provided_user:
#         context['user_obj'] = user_obj = provided_user
#     else:
#         raise logic.NotFound
#
#     _check_access('user_show', context, data_dict)
#
#     user_dict = model_dictize.user_dictize(user_obj, context)
#
#     if context.get('return_minimal'):
#         return user_dict
#
#     revisions_q = model.Session.query(model.Revision
#                                       ).filter_by(author=user_obj.name)
#
#     revisions_list = []
#     for revision in revisions_q.limit(20).all():
#         revision_dict = tk.get_action('revision_show')(context, {'id': revision.id})
#         revision_dict['state'] = revision.state
#         revisions_list.append(revision_dict)
#     user_dict['activity'] = revisions_list
#
#     offset = data_dict.get('offset', 0)
#     limit = data_dict.get('limit', 20)
#     print data_dict.get('sort', None)
#     sort = data_dict.get('sort', 'metadata_modified desc')
#     user_dict['datasets'] = []
#     dataset_q = model.Session.query(model.Package).join(model.PackageRole).filter_by(user=user_obj,
#                                                                                      role=model.Role.ADMIN
#                                                                                      ).order_by(sort).offset(
#         offset).limit(limit)
#
#     dataset_q_counter = model.Session.query(model.Package).join(model.PackageRole
#                                                                 ).filter_by(user=user_obj, role=model.Role.ADMIN
#                                                                             ).count()
#
#     for dataset in dataset_q:
#         try:
#             dataset_dict = tk.get_action('package_show')(context, {'id': dataset.id})
#         except tk.NotAuthorized:
#             continue
#         user_dict['datasets'].append(dataset_dict)
#
#     user_dict['num_followers'] = tk.get_action('user_follower_count')(
#         {'model': model, 'session': model.Session},
#         {'id': user_dict['id']})
#     user_dict['total_count'] = dataset_q_counter
#     return user_dict
