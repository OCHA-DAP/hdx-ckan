import exceptions as exceptions
import logging as logging

import ckanext.hdx_users.controllers.mailer as hdx_mailer
import ckanext.hdx_users.model as umodel
import pylons.config as config

import ckan.lib.helpers as h
import ckan.logic as logic

log = logging.getLogger(__name__)

NotFound = logic.NotFound


def token_show(context, user):
    id = user.get('id')
    token_obj = umodel.ValidationToken.get(user_id=id)
    if token_obj is None:
        raise NotFound
    return token_obj.as_dict()


def token_show_by_id(context, data_dict):
    token = data_dict.get('token', None)
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    return token_obj.as_dict()


def token_update(context, data_dict):
    token = data_dict.get('token')
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    session = context["session"]
    token_obj.valid = True
    session.add(token_obj)
    session.commit()
    return token_obj.as_dict()


def send_validation_email(user, token):
    validate_link = h.url_for(
        controller='ckanext.hdx_users.controllers.mail_validation_controller:ValidationController',
        action='validate',
        token=token['token'])
    link = '{0}{1}'
    subject = "HDX: Complete your registration"
    print 'Validate link: ' + validate_link
    html = """\
            <p>Hello,</p> 
            <br/>
            <p>Thank you for your interest in the <a href="https://data.humdata.org/">Humanitarian Data Exchange (HDX)</a>. Please complete the registration process by clicking the link below.</p>
            <br/>
            <p><a href="{link}">Verify Email</a></p>
            <br/>
            <p>Best wishes,</p>
            <p>The HDX team</p>
        """.format(link=link.format(config['ckan.site_url'], validate_link))

    try:
        hdx_mailer.mail_recipient([{'email': user['email']}], subject, html)
        return True
    except exceptions.Exception, e:
        error_summary = str(e)
        log.error(error_summary)
        return False
