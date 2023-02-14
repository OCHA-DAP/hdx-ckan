import json

from flask import Blueprint

import ckan.model as model
import ckanext.hdx_users.helpers.mailer as hdx_mailer
from ckan import logic
from ckan.plugins import toolkit as tk
from ckanext.requestdata.view_helper import process_extras_fields

get_action = tk.get_action
NotFound = tk.ObjectNotFound
NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError
abort = tk.abort
g = tk.g
config = tk.config
_ = tk._
h = tk.h
url_for = tk.url_for
request = tk.request

requestdata_send_request = Blueprint(u'requestdata_send_request', __name__)


def _get_sysadmins():
    q = model.Session.query(model.User).filter(model.User.sysadmin == True,
                                               model.User.state == 'active')
    return q.all()


def _get_context():
    return {
        'model': model,
        'session': model.Session,
        'user': g.user,
        'auth_user_obj': g.userobj
    }


def _get_action(action, data_dict):
    return get_action(action)(_get_context(), data_dict)


def _get_email_configuration(
    user_name, data_owner, dataset_name, email, message, organization,
    data_maintainers, data_maintainers_ids, only_org_admins=False):
    schema = logic.schema.update_configuration_schema()
    available_terms = ['{name}', '{data_maintainers}', '{dataset}',
                       '{organization}', '{message}', '{email}']
    new_terms = [user_name, data_maintainers, dataset_name, organization,
                 message, email]

    is_user_sysadmin = g.userobj.sysadmin

    for key in schema:
        # get only email configuration
        if 'email_header' in key:
            email_header = config.get(key)
        elif 'email_body' in key:
            email_body = config.get(key)
        elif 'email_footer' in key:
            email_footer = config.get(key)
    if '{message}' not in email_body and not email_body and not email_footer:
        email_body += message
        return email_body
    for i in range(0, len(available_terms)):
        if available_terms[i] == '{dataset}' and new_terms[i]:
            url = tk.url_for(
                controller='package',
                action='read',
                id=new_terms[i], qualified=True)
            new_terms[i] = '<a href="' + url + '">' + new_terms[i] + '</a>'
        elif available_terms[i] == '{organization}' and is_user_sysadmin:
            new_terms[i] = config.get('ckan.site_title')
        elif available_terms[i] == '{data_maintainers}':
            if len(new_terms[i]) == 1:
                new_terms[i] = new_terms[i][0]
            else:
                maintainers = ''
                for j, term in enumerate(new_terms[i][:]):
                    maintainers += term

                    if j == len(new_terms[i]) - 2:
                        maintainers += ' and '
                    elif j < len(new_terms[i]) - 1:
                        maintainers += ', '

                new_terms[i] = maintainers
        elif available_terms[i] == '{email}':
            # display a mask of the email
            email_list = new_terms[i].split('@')
            new_terms[i] = "@".join(
                [email_list[0].replace(email_list[0][1:len(email_list[0]) - 1], '********'), email_list[1]])
        email_header = email_header.replace(available_terms[i], new_terms[i])
        email_body = email_body.replace(available_terms[i], new_terms[i])
        email_footer = email_footer.replace(available_terms[i], new_terms[i])

    if only_org_admins:
        owner_org = _get_action('package_show',
                                {'id': dataset_name}).get('owner_org')
        url = url_for('requestdata_organization_requests.requested_data',
                      id=owner_org, qualified=True)
        email_body += '<br><br> This dataset\'s maintainer does not exist.\
         Go to your organisation\'s <a href="' + url + '">Requested Data</a>\
          page to see the new request. Please also edit the dataset and assign\
           a new maintainer.'
    else:
        if len(data_maintainers_ids) > 1:
            owner_org = _get_action('package_show', {'id': dataset_name}).get('owner_org')
            url = url_for('requestdata_organization_requests.requested_data', id=owner_org, qualified=True)
        else:
            url = url_for('requestdata.my_requested_data', id=data_maintainers_ids[0], qualified=True)
        email_body += '<br><br><strong> Please accept or decline the request\
         as soon as you can by visiting the \
         <a href="' + url + '">My Requests</a> page.</strong>'

    organizations = \
        _get_action('hdx_organization_list_for_user', {'id': data_owner})

    package = _get_action('package_show', {'id': dataset_name})

    if not only_org_admins:
        for org in organizations:
            if org['name'] in organization and package['owner_org'] == org['id']:
                url = \
                    url_for('requestdata_organization_requests.requested_data',
                            id=org['name'], qualified=True)
                email_body += '<br><br> Go to <a href="' + url + '">Requested data</a> page in organization admin.'

    site_url = config.get('ckan.site_url')
    site_title = config.get('ckan.site_title')
    newsletter_url = config.get('ckanext.requestdata.newsletter_url', site_url)
    twitter_url = \
        config.get('ckanext.requestdata.twitter_url', 'https://twitter.com')
    contact_email = config.get('ckanext.requestdata.contact_email', '')

    email_footer += """
        <br/><br/>
        <small>
          <p>
            <a href=" """ + site_url + """ ">""" + site_title + """</a>
          </p>
          <p>
            <a href=" """ + newsletter_url + """ ">\
            Sign up for our newsletter</a> | \
            <a href=" """ + twitter_url + """ ">Follow us on Twitter</a>\
             | <a href="mailto:""" + contact_email + """ ">Contact us</a>
          </p>
        </small>

    """

    result = email_header + '<br><br>' + email_body + '<br><br>' + email_footer

    return result


def send_request():
    '''Send mail to resource owner.

    :param data: Contact form data.
    :type data: object

    :rtype: json
    '''
    context = {'model': model, 'session': model.Session,
               'user': g.user, 'auth_user_obj': g.userobj}
    try:
        if request.method == 'POST':
            data = request.form.to_dict()
            _get_action('requestdata_request_create', data)
        else:
            abort(403, _('Unauthorized to access this page'))
    except NotAuthorized:
        abort(403, _('Unauthorized to update this dataset.'))
    except ValidationError as e:
        error = {
            'success': False,
            'error': {
                'fields': e.error_dict
            }
        }

        return json.dumps(error)

    data_dict = {'id': data['package_id']}
    package = _get_action('package_show', data_dict)

    sender_name = data.get('sender_name', '')
    sender_email = data.get('email_address', '')

    user_obj = context['auth_user_obj']
    data_dict = {
        'id': user_obj.id,
        'permission': 'read'
    }

    organizations = _get_action('organization_list_for_user', data_dict)
    try:
        sender_org = _get_action('organization_show', {'id': data.get('sender_organization_id')})
    except NotFound:
        sender_org = None

    extras = json.loads(process_extras_fields(data, organizations, sender_org))

    orgs = []
    for i in organizations:
        orgs.append(i['display_name'])
    org = ','.join(orgs)
    dataset_name = package['name']
    dataset_title = package['title']
    email = user_obj.email
    message = data['message_content']
    creator_user_id = package['creator_user_id']
    data_owner = \
        _get_action('user_show', {'id': creator_user_id}).get('name')
    _sysadmins = _get_sysadmins()
    if len(_sysadmins) > 0:
        sysadmin = _sysadmins[0].name
        context_sysadmin = {
            'model': model,
            'session': model.Session,
            'user': sysadmin,
            'auth_user_obj': g.userobj
        }
        to = package['maintainer']
        if to is None:
            message = {
                'success': False,
                'error': {
                    'fields': {
                        'email': 'Dataset maintainer email not found.'
                    }
                }
            }

            return json.dumps(message)
        maintainers = to.split(',')
        data_dict = {
            'users': []
        }
        users_email = []
        only_org_admins = False
        data_maintainers = []
        data_maintainers_ids = []
        # Get users objects from maintainers list
        user = {}
        for id in maintainers:
            try:
                user = get_action('user_show')(context_sysadmin, {'id': id})
                data_dict['users'].append(user)
                users_email.append({'display_name': user.get('fullname'), 'email': user.get('email')})
                data_maintainers.append(user['fullname'] or user['name'])
                data_maintainers_ids.append(user['name'] or user['id'])
            except NotFound:
                pass
        mail_subject = \
            config.get('ckan.site_title') + ': New data request "' \
            + dataset_title + '"'

        if len(users_email) == 0:
            admins = _org_admins_for_dataset(dataset_name)
            # admins=og_create.get_organization_admins(package.get('owner_org'))

            for admin in admins:
                users_email.append({'display_name': admin.get('fullname'), 'email': admin.get('email')})
                data_maintainers.append(admin.get('fullname'))
                data_maintainers_ids.append(admin.get('name') or admin.get('id'))
            only_org_admins = True

        subject = sender_name + u' has requested access to one of your datasets'
        email_data = {
            'user_fullname': sender_name,
            'user_email': email,
            'msg': message,
            'extras': extras,
            'org_name': package.get('organization').get('title'),
            'dataset_link': h.url_for('dataset_read', id=dataset_name, qualified=True),
            'dataset_title': dataset_title,
            'maintainer_fullname': user.get('display_name') or user.get('fullname') if user else 'HDX user',
            'requestdata_org_url': h.url_for('requestdata_organization_requests.requested_data',
                                             id=package.get('owner_org'),
                                             qualified=True)
        }
        hdx_mailer.mail_recipient(users_email, subject, email_data, footer='hdx@un.org',
                                  snippet='email/content/request_data_to_admins.html')

        subject = u'Request for access to metadata-only dataset'
        email_data = {
            'user_fullname': sender_name,
            'msg': message,
            'org_name': package.get('organization').get('title'),
            'dataset_link': h.url_for('dataset_read', id=dataset_name, qualified=True),
            'dataset_title': dataset_title,
        }
        senders_email = [{'display_name': sender_name, 'email': sender_email}]
        hdx_mailer.mail_recipient(senders_email, subject, email_data, footer=email,
                                  snippet='email/content/request_data_to_user.html')

        # notify package creator that new data request was made
        _get_action('requestdata_notification_create', data_dict)
        data_dict = {
            'package_id': data['package_id'],
            'flag': 'request'
        }

        action_name = 'requestdata_increment_request_data_counters'
        _get_action(action_name, data_dict)
        response_dict = {
            'success': True,
            'message': 'Email message was successfully sent.'
        }
        return json.dumps(response_dict)
    else:
        message = {
            'success': True,
            'message': 'Request sent, but email message was not sent.'
        }

        return json.dumps(message)


def _org_admins_for_dataset(dataset_name):
    package = _get_action('package_show', {'id': dataset_name})
    owner_org = package['owner_org']
    admins = []

    org = _get_action('organization_show', {'id': owner_org})

    for user in org['users']:
        if user['capacity'] == 'admin':
            db_user = model.User.get(user['id'])
            data = {
                'email': db_user.email,
                'fullname': db_user.fullname or db_user.name
            }
            admins.append(data)

    return admins


requestdata_send_request.add_url_rule(u'/request_data', view_func=send_request, methods=(u'GET', u'POST',))
