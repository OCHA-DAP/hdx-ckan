import json
import logging

import ckan.lib.navl.dictization_functions as dictization_functions
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.mailer as hdx_mailer
from ckan.types import Context, DataDict, Request
from ckan.lib.navl.dictization_functions import validate
from ckanext.requestdata.logic.schema import request_create_schema
from ckanext.requestdata.view_helper import process_extras_fields

get_action = tk.get_action
check_access = tk.check_access
config = tk.config
h = tk.h
g = tk.g
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
unicode_safe = tk.get_validator('unicode_safe')
log = logging.getLogger(__name__)


class DatasetRequestAccessLogic(object):
    def __init__(self, context: Context, request: Request):
        self.request = request
        self.context = context
        self.form = request.form
        self.schema = request_create_schema()

    def read(self) -> DataDict:
        data_dict = logic.clean_dict(dictization_functions.unflatten(logic.tuplize_dict(logic.parse_params(self.form))))
        return data_dict

    def validate(self, data_dict: DataDict):
        try:
            validated_response = validate(data_dict, self.schema, self.context)
        except Exception as ex:
            log.error(ex)

        return validated_response

    def send_request(self) -> tuple[bool, str]:
        data = self.request.form.to_dict()
        get_action('requestdata_request_create')(self.context, data)

        pkg_dict = get_action('package_show')(self.context, {'id': data['package_id']})

        maintainer_id = pkg_dict['maintainer']
        if maintainer_id is None:
            return False, 'Dataset maintainer email not found.'

        user_obj = self.context['auth_user_obj']

        # Get users objects from maintainers list
        context_user_show = {
            'model': model,
            'session': model.Session,
            'user': g.user,
            'auth_user_obj': g.userobj,
            'keep_email': True,
        }

        data_dict = {
            'users': []
        }
        recipients = []
        maintainer_dict = {}
        try:
            maintainer_dict = get_action('user_show')(context_user_show, {'id': maintainer_id})
            data_dict['users'].append(maintainer_dict)
            recipients.append({'display_name': maintainer_dict.get('fullname'), 'email': maintainer_dict.get('email')})
        except NotFound:
            pass

        if len(recipients) == 0:
            admins = _org_admins_for_dataset(self.context, pkg_dict['name'])

            for admin in admins:
                recipients.append({'display_name': admin.get('fullname'), 'email': admin.get('email')})

        sender_name = data.get('sender_name', '')
        sender_email = data.get('email_address', '')
        user_email = user_obj.email
        message = data['message_content']

        try:
            sender_org = get_action('organization_show')(self.context, {'id': data.get('sender_organization_id')})
        except NotFound:
            sender_org = None

        organizations = get_action('organization_list_for_user')(self.context, {
            'id': user_obj.id,
            'permission': 'read'
        })
        extras = json.loads(process_extras_fields(data, organizations, sender_org))

        _send_email_to_maintainer(sender_name, message, user_email, extras, recipients, maintainer_dict, pkg_dict)
        _send_email_to_requester(sender_name, sender_email, message, user_email, pkg_dict)

        # notify package creator that new data request was made
        get_action('requestdata_notification_create')(self.context, data_dict)

        data_dict = {
            'package_id': data['package_id'],
            'flag': 'request'
        }
        get_action('requestdata_increment_request_data_counters')(self.context, data_dict)

        return True, 'Email message was successfully sent.'


def _org_admins_for_dataset(context: Context, dataset_name: str):
    pkg_dict = get_action('package_show')(context, {'id': dataset_name})
    owner_org = pkg_dict['owner_org']

    org = get_action('organization_show')(context, {'id': owner_org})

    admins = []
    for user in org['users']:
        if user['capacity'] == 'admin':
            db_user = model.User.get(user['id'])
            data = {
                'email': db_user.email,
                'fullname': db_user.fullname or db_user.name
            }
            admins.append(data)

    return admins


def _send_email_to_requester(sender_name: str, sender_email: str, message: str, user_email: str,
                             pkg_dict: DataDict) -> None:
    subject = u'Request for access to metadata-only dataset'
    email_data = {
        'user_fullname': sender_name,
        'msg': message,
        'org_name': pkg_dict.get('organization').get('title'),
        'dataset_link': h.url_for('dataset_read', id=pkg_dict['name'], qualified=True),
        'dataset_title': pkg_dict['title'],
    }
    senders_email = [{'display_name': sender_name, 'email': sender_email}]
    hdx_mailer.mail_recipient(senders_email, subject, email_data, footer=user_email,
                              snippet='email/content/request_data_to_user.html')


def _send_email_to_maintainer(sender_name: str, message: str, user_email: str, extras, recipients,
                              maintainer_dict: DataDict, pkg_dict: DataDict):
    subject = sender_name + u' has requested access to one of your datasets: ' + pkg_dict['title']
    email_data = {
        'user_fullname': sender_name,
        'user_email': user_email,
        'msg': message,
        'extras': extras,
        'org_name': pkg_dict.get('organization').get('title'),
        'dataset_link': h.url_for('dataset_read', id=pkg_dict['name'], qualified=True),
        'dataset_title': pkg_dict['title'],
        'maintainer_fullname': maintainer_dict.get('display_name') or maintainer_dict.get(
            'fullname') if maintainer_dict else 'HDX user',
        'requestdata_org_url': h.url_for('requestdata_organization_requests.requested_data',
                                         id=pkg_dict.get('owner_org'), qualified=True)
    }
    hdx_mailer.mail_recipient(recipients, subject, email_data, footer='hdx@un.org',
                              snippet='email/content/request_data_to_admins.html')
