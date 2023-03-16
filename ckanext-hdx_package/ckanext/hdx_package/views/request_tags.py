import json
import logging
import requests
import ckan.lib.captcha as captcha
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.helpers as usr_h

from flask import Blueprint, make_response
from six import text_type
from ckan.common import config
from ckan.views.api import CONTENT_TYPES
from ckan.lib.mailer import MailerException
from ckanext.hdx_theme.util.mail import hdx_validate_email

hdx_request_tags = Blueprint(u'hdx_request_tags', __name__, url_prefix=u'/request_tags')

log = logging.getLogger(__name__)
is_valid_captcha = usr_h.validate_captcha
get_action = tk.get_action
check_access = tk.check_access
request = tk.request
_ = tk._
g = tk.g
NotAuthorized = tk.NotAuthorized
ValidationError = tk.ValidationError


def _build_json_response(data_dict, status=200):
    headers = {
        'Content-Type': CONTENT_TYPES['json'],
    }
    body = json.dumps(data_dict)
    response = make_response((body, status, headers))
    return response


def _process_tags_request():
    data = {
        'fullname': request.form.get('fullname', ''),
        'email': request.form.get('email', ''),
        'suggested_tags': request.form.get('suggested_tags', ''),
        'datatype': request.form.get('datatype', ''),
        'comment': request.form.get('comment', '')
    }
    return data


def _validate_tags_request_fields(data):
    errors = {}
    for field in ['fullname', 'email', 'suggested_tags', 'datatype', 'comment']:
        if not data[field] or data[field].strip() in ['', '-1']:
            errors[field] = u'Should not be empty'

    if len(errors) > 0:
        raise ValidationError(errors)


def _validate_tags_request_email_field(email):
    errors = {}
    try:
        hdx_validate_email(email)
    except Exception:
        errors['email'] = u'Please provide a valid email address'
        raise ValidationError(errors)


def _validate_tags_request_tags_field(tags, approved_tags):
    errors = {}

    existing_tags = []
    for tag in tags.split(','):
        if tag.lower() in approved_tags:
            existing_tags.append(tag)

    no_existing_tags = len(existing_tags)
    if no_existing_tags > 1:
        errors['suggested_tags'] = u'%s already exist' % ', '.join(existing_tags)
        errors['existing_tags'] = existing_tags
    elif no_existing_tags == 1:
        errors['suggested_tags'] = u'%s already exists' % existing_tags[0]
        errors['existing_tags'] = existing_tags

    if len(errors) > 0:
        raise ValidationError(errors)


def request_tags():
    '''
    Send new tag(s) request form
    :return:
    '''

    context = {
        'model': model,
        'session': model.Session,
        'user': g.user,
        'auth_user_obj': g.userobj
    }

    data_dict = {}

    try:
        usr_h.is_valid_captcha(request.form.get('g-recaptcha-response'))

        check_access('hdx_send_mail_request_tags', context, data_dict)

        data_dict = _process_tags_request()
        approved_tags = get_action('hdx_tag_approved_list')(context, {})

        _validate_tags_request_tags_field(data_dict['suggested_tags'], approved_tags)
        _validate_tags_request_fields(data_dict)
        _validate_tags_request_email_field(data_dict['email'])

    except NotAuthorized:
        return _build_json_response(
            {'success': False, 'error': {'message': u'You have to log in before sending a contact request.'}})
    except ValidationError as e:
        resp = {'success': False, 'error': {'message': u'Validation error. Please try again.', 'fields': e.error_dict}}
        if e.error_dict and e.error_dict.get('existing_tags'):
            resp['error']['existing_tags'] = e.error_dict['existing_tags']
            del e.error_dict['existing_tags']
        return _build_json_response(resp)
    except captcha.CaptchaError:
        return _build_json_response(
            {'success': False, 'error': {'message': u'Bad Captcha. Please try again.'}})
    except Exception as e:
        log.error(e)
        return _build_json_response({'success': False, 'error': {'message': str(e)}})

    try:
        get_action('hdx_send_mail_request_tags')(context, data_dict)
    except MailerException as e:
        return _build_json_response(
            {'success': False, 'error': {'message': u'Could not send request for: %s.' % text_type(e)}})
    except Exception as e:
        log.error(e)
        return _build_json_response(
            {'success': False, 'error': {'message': u'There was an error. Please contact support.'}})
    return _build_json_response({'success': True})


hdx_request_tags.add_url_rule(u'/suggest', view_func=request_tags, methods=[u'POST'])
