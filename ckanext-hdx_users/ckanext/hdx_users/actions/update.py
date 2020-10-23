import ckan.model as model
import pylons.config as config

import ckan.logic as logic
import ckanext.hdx_users.model as umodel

import ckanext.hdx_users.helpers.reset_password as reset_password
import ckanext.hdx_users.controllers.mailer as hdx_mailer


NotFound = logic.NotFound
_check_access = logic.check_access
get_action = logic.get_action


def token_update(context, data_dict):
    token = data_dict.get('token')
    token_obj = umodel.ValidationToken.get_by_token(token=token)
    if token_obj is None:
        raise NotFound
    # Logged in user should have edit access to account token belongs to
    _check_access('user_update', context, {'id': token_obj.user_id})
    session = context["session"]
    token_obj.valid = True
    session.add(token_obj)
    session.commit()
    return token_obj.as_dict()


def user_fullname_update(context, data_dict):
    # Logged in user should have edit access to account token belongs to
    _check_access('user_update', context, {'id': data_dict.get('id')})
    first_name = data_dict.get('first_name')
    last_name = data_dict.get('last_name')
    fullname = first_name + ' ' + last_name
    user_obj = model.User.get(data_dict.get('id'))
    if not user_obj:
        raise NotFound('User id not found')
    ue_data_dict = {'user_id': user_obj.id, 'extras': [
        {'key': umodel.HDX_FIRST_NAME, 'new_value': first_name},
        {'key': umodel.HDX_LAST_NAME, 'new_value': last_name},
    ]}
    ue_result = get_action('user_extra_update')(context, ue_data_dict)
    return ue_result


def hdx_send_reset_link(context, data_dict):
    from urlparse import urljoin
    import ckan.lib.helpers as h

    model = context['model']

    user = None
    reset_link = None
    user_fullname = None
    recipient_mail = None

    id = data_dict.get('id', None)
    if id:
        user = model.User.get(id)
        context['user_obj'] = user
        if user is None:
            raise NotFound

    expiration_in_hours = int(config.get('hdx.password.reset_key.expiration_in_hours', 3))
    if user:
        reset_password.create_reset_key(user, expiration_in_hours)

        recipient_mail = user.email if user.email else None
        user_fullname = user.fullname or ''
        reset_link = urljoin(config.get('ckan.site_url'),
                             h.url_for(controller='user', action='perform_reset', id=user.id, key=user.reset_key))

    # body = u"""\
    #             <p>Dear {fullname}, </p>
    #             <p>You have requested your password on {site_title} to be reset.</p>
    #             <p>Please click on the following link to confirm this request:</p>
    #             <p> <a href=\"{reset_link}\">{reset_link}</a></p>
    #         """.format(fullname=user_fullname, site_title=config.get('ckan.site_title'),
    #                    reset_link=reset_link)

    email_data = {
        'user_fullname': user_fullname,
        'user_reset_link': reset_link,
        'expiration_in_hours': expiration_in_hours,
    }
    if recipient_mail:
        subject = u'HDX password reset'
        hdx_mailer.mail_recipient([{'display_name': user_fullname, 'email': recipient_mail}], subject,
                                  email_data, footer=recipient_mail,
                                  snippet='email/content/password_reset.html')
        # hdx_mailer.mail_recipient([{'display_name': user_fullname, 'email': recipient_mail}], subject, body)

