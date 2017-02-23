import ckanext.hdx_users.model as umodel
import ckan.logic as logic
import pylons.config as config
import ckan.lib.helpers as h
import ckanext.hdx_users.controllers.mailer as hdx_mailer
import exceptions as exceptions
import logging as logging

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
    subject = "Please verify your email for HDX registration"
    print 'Validate link: ' + validate_link
    html = """\
            <p>Thank you for your interest in HDX. In order to continue registering your account, please verify your email address by simply clicking below.</p>
            <p><a href="{link}">Verify Email</a></p>
        """.format(link=link.format(config['ckan.site_url'], validate_link))

    try:
        hdx_mailer.mail_recipient([{'display_name': 'User', 'email': user['email']}], subject, html)
        return True
    except exceptions.Exception, e:
        error_summary = str(e)
        log.error(error_summary)
        return False
