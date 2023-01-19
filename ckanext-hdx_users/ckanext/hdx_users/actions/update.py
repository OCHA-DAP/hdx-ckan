import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.hdx_users.helpers.mailer as hdx_mailer
import ckanext.hdx_users.helpers.reset_password as reset_password
import ckanext.hdx_users.model as umodel
from ckanext.hdx_users.helpers.token_expiration_helper import find_expiring_api_tokens, send_emails_for_expiring_tokens

NotFound = tk.ObjectNotFound
_check_access = tk.check_access
_get_or_bust = tk.get_or_bust
ValidationError = tk.ValidationError
get_action = tk.get_action
config = tk.config


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
    from six.moves.urllib.parse import urljoin

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

    expiration_in_minutes = int(config.get('hdx.password.reset_key.expiration_in_minutes', 20))
    if user:
        reset_password.create_reset_key(user, expiration_in_minutes)

        recipient_mail = user.email if user.email else None
        user_fullname = user.fullname or ''
        reset_link = urljoin(config.get('ckan.site_url'),
                             h.url_for(controller='user', action='perform_reset', id=user.id, key=user.reset_key))

    email_data = {
        'user_fullname': user_fullname,
        'user_reset_link': reset_link,
        'expiration_in_minutes': expiration_in_minutes,
    }
    if recipient_mail:
        subject = u'HDX password reset'
        hdx_mailer.mail_recipient([{'display_name': user_fullname, 'email': recipient_mail}], subject,
                                  email_data, footer=recipient_mail,
                                  snippet='email/content/password_reset.html')


def notify_users_about_api_token_expiration(context, data_dict):
    '''
    :param days_in_advance: how many days in advance we should look for expiring api tokens
    :type days_in_advance: int
    :param expires_on_specified_day: if True then we're looking only for api tokens that will expire on the
        specified day. Otherwise, we look for tokens that expire from now till the specified day.
    :type expires_on_specified_day: bool
    :return: number of api tokens that will expire
    '''
    _check_access('notify_users_about_api_token_expiration', context, {})
    days_in_advance, expires_on_specified_day = __extract_token_expiration_params(data_dict)

    model = context['model']
    session = context['model'].Session

    token_info_list, period_start_string, period_end_string = \
        find_expiring_api_tokens(model, session, days_in_advance, expires_on_specified_day)
    number_of_emails = send_emails_for_expiring_tokens(token_info_list)
    return {
        'start_date': period_start_string,
        'end_date': period_end_string,
        'emails_sent': number_of_emails,
    }


def __extract_token_expiration_params(data_dict):
    days_in_advance = _get_or_bust(data_dict, 'days_in_advance')
    try:
        days_in_advance = int(days_in_advance)
        expires_on_specified_day = data_dict.get('expires_on_specified_day') == 'true' \
                                   or data_dict.get('expires_on_specified_day') is True
    except ValueError:
        raise ValidationError('Limit must be a positive integer')
    return days_in_advance, expires_on_specified_day
