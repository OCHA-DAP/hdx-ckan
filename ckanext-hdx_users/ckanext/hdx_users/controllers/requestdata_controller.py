import json
import ckan.model as model
import ckanext.requestdata.controllers.user as requestdata_user
from ckanext.requestdata.emailer import send_email
from email_validator import validate_email
from paste.deploy.converters import asbool
from pylons import config

from ckan import logic
from ckan.common import _
from ckan.lib import base
from ckan.plugins import toolkit

get_action = logic.get_action
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
ValidationError = logic.ValidationError
_get_action = requestdata_user._get_action()
abort = base.abort

_SUBJECT_REQUESTDATA_REPLY = u'''[HDX] Data request reply: "{dataset_title}" '''
_MESSAGE_REQUESTDATA_REPLY = \
    u'''
    Dear {requested_by},
    {maintainer_name} from {organization} replied to your request for "{package_name}". See their message below:<br/>
    
    {message_content}

    Best wishes, <br/>
    the HDX Team <br/>
    '''


class HDXRequestdataController(requestdata_user.UserController):
    def handle_new_request_action(self, username, request_action):
        '''Handles sending email to the person who created the request, as well
        as updating the state of the request depending on the data sent.

        :param username: The user's name.
        :type username: string

        :param request_action: The current action. Can be either reply or
        reject
        :type request_action: string

        :rtype: json

        '''

        data = dict(toolkit.request.POST)

        if request_action == 'reply':
            reply_email = data.get('email')

            try:
                validate_email(reply_email)
            except Exception:
                error = {
                    'success': False,
                    'error': {
                        'fields': {
                            'email': 'The email you provided is invalid.'
                        }
                    }
                }

                return json.dumps(error)

        counters_data_dict = {
            'package_id': data['package_id'],
            'flag': ''
        }
        if 'rejected' in data:
            data['rejected'] = asbool(data['rejected'])
            counters_data_dict['flag'] = 'declined'
        elif 'data_shared' in data:
            counters_data_dict['flag'] = 'shared and replied'
        else:
            counters_data_dict['flag'] = 'replied'

        message_content = self._get_email_content(data, request_action)

        if message_content is None or message_content == '':
            payload = {
                'success': False,
                'error': {
                    'message_content': 'Missing value'
                }
            }

            return json.dumps(payload)

        try:
            _get_action('requestdata_request_patch', data)
        except NotAuthorized:
            abort(403, _('Not authorized to use this action.'))
        except ValidationError as e:
            error = {
                'success': False,
                'error': {
                    'fields': e.error_dict
                }
            }

            return json.dumps(error)

        to = self._get_email_to(data, request_action)

        subject = self._get_email_subject(data, request_action)

        file = data.get('file_upload')

        response = send_email(message_content, to, subject, file=file)

        if response['success'] is False:
            error = {
                'success': False,
                'error': {
                    'fields': {
                        'email': response['message']
                    }
                }
            }

            return json.dumps(error)

        success = {
            'success': True,
            'message': 'Message was sent successfully'
        }

        action_name = 'requestdata_increment_request_data_counters'
        _get_action(action_name, counters_data_dict)

        return json.dumps(success)

    def _get_email_content(self, data_dict, request_action):
        message_content = data_dict.get('message_content')
        if message_content is None or message_content == '':
            return None
        # if request_action == 'reply':
        #     message_content += '<br><br> You can contact the maintainer on ' \
        #                        'this email address: ' + reply_email
        user_obj = model.User.get(data_dict.get('sender_id'))
        pkg_obj = model.Package.get(data_dict.get('package_id'))
        org_obj = model.Group.get(pkg_obj.owner_org)
        email_content = _MESSAGE_REQUESTDATA_REPLY.format(**{
            'requested_by': data_dict.get('requested_by'),
            'maintainer_name': user_obj.display_name,
            'organization': org_obj.display_name,
            'package_name': data_dict.get('package_name'),
            'message_content': message_content,
        })

        return email_content

    def _get_email_to(self, data_dict, request_action):
        to = data_dict['send_to']
        return to

    def _get_email_subject(self, data_dict, request_action):
        subject = config.get('ckan.site_title') + ': Data request ' + \
                  request_action
        return subject
