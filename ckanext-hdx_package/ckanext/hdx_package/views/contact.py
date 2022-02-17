import json
import logging

from flask import Blueprint, make_response
from six import text_type

import ckan.lib.captcha as captcha
import ckan.model as model
import ckan.plugins.toolkit as tk

from ckan.views.api import CONTENT_TYPES
from ckan.lib.mailer import MailerException

import ckanext.hdx_package.helpers.membership_data as membership_data
import ckanext.hdx_users.helpers.helpers as usr_h

from ckanext.hdx_theme.util.mail import hdx_validate_email

log = logging.getLogger(__name__)

config = tk.config
get_action = tk.get_action
check_access = tk.check_access
request = tk.request
render = tk.render
abort = tk.abort
redirect = tk.redirect_to
_ = tk._
h = tk.h
g = tk.g

NotAuthorized = tk.NotAuthorized

hdx_contact = Blueprint(u'hdx_contact', __name__, url_prefix=u'/membership')


def _build_json_response(data_dict, status=200):
    headers = {
        'Content-Type': CONTENT_TYPES['json'],
    }
    body = json.dumps(data_dict)
    response = make_response((body, status, headers))
    return response


def contact_contributor():
    '''
    Send a contact request form
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

        check_access('hdx_send_mail_contributor', context, data_dict)
        # for k, v in membership_data.get('contributor_topics').iteritems():
        #     if v == request.form.get('topic'):
        #         data_dict['topic'] = v
        data_dict['topic'] = request.form.get('topic')
        data_dict['fullname'] = request.form.get('fullname')
        data_dict['email'] = request.form.get('email')
        data_dict['msg'] = request.form.get('msg')
        data_dict['pkg_owner_org'] = request.form.get('pkg_owner_org')
        data_dict['pkg_title'] = request.form.get('pkg_title')
        data_dict['pkg_id'] = request.form.get('pkg_id')
        data_dict['pkg_url'] = h.url_for('dataset_read', id=request.form.get('pkg_id'), qualified=True)
        data_dict['hdx_email'] = config.get('hdx.faqrequest.email', 'hdx@humdata.org')

        hdx_validate_email(data_dict['email'])

    except NotAuthorized:
        return _build_json_response(
            {'success': False, 'error': {'message': u'You have to log in before sending a contact request'}})
    except captcha.CaptchaError:
        return _build_json_response(
            {'success': False, 'error': {'message': _(u'Bad Captcha. Please try again.')}})
    except Exception as e:
        log.error(e)
        return _build_json_response({'success': False, 'error': {'message': u'There was an error. Please contact support'}})

    try:
        get_action('hdx_send_mail_contributor')(context, data_dict)
    except MailerException as e:
        error_summary = _('Could not send request for: %s') % text_type(e)
        log.error(error_summary)
        return _build_json_response({'success': False, 'error': {'message': error_summary}})
    except Exception as e:
        # error_summary = e.error or str(e)
        log.error(e)
        return _build_json_response({'success': False, 'error': {'message': u'There was an error. Please contact support'}})
    return _build_json_response({'success': True})


def contact_members():
    '''
    Send a contact request form
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
        _captcha = usr_h.is_valid_captcha(request.form.get('g-recaptcha-response'))
        source_type = request.form.get('source_type')
        data_dict['source_type'] = source_type
        org_id = request.form.get('org_id')
        check_access('hdx_send_mail_members', context, {'org_id': org_id})
        data_dict['topic_key'] = request.form.get('topic')
        data_dict['topic'] = membership_data.membership_data.get('group_topics').get(request.form.get('topic'))
        data_dict['fullname'] = request.form.get('fullname')
        data_dict['email'] = request.form.get('email')
        data_dict['msg'] = request.form.get('msg')
        data_dict['pkg_owner_org_id'] = org_id
        try:
            owner_org = get_action("organization_show")(context, {'id': org_id, 'include_datasets': False})
            data_dict['pkg_owner_org'] = owner_org.get("display_name") or owner_org.get("title")
        except Exception as e:
            data_dict['pkg_owner_org'] = org_id
        data_dict['pkg_title'] = request.form.get('title')
        if source_type == 'dataset':
            data_dict['pkg_id'] = request.form.get('pkg_id')
            data_dict['pkg_url'] = h.url_for('dataset_read', id=request.form.get('pkg_id'),
                                             qualified=True)
        data_dict['hdx_email'] = config.get('hdx.faqrequest.email', 'hdx@humdata.org')

        hdx_validate_email(data_dict['email'])

        get_action('hdx_send_mail_members')(context, data_dict)

    except NotAuthorized:
        return _build_json_response(
            {'success': False, 'error': {'message': 'You have to log in before sending a contact request'}})
    except captcha.CaptchaError:
        return _build_json_response(
            {'success': False, 'error': {'message': _(u'Bad Captcha. Please try again.')}})
    except Exception as e:
        error_summary = str(e)
        return _build_json_response({'success': False, 'error': {'message': error_summary}})

    return _build_json_response({'success': True})


hdx_contact.add_url_rule(u'/contact_contributor', view_func=contact_contributor, methods=[u'POST'])
hdx_contact.add_url_rule(u'/contact_members', view_func=contact_members, methods=[u'POST'])
