import datetime

from sqlalchemy import and_
from sqlalchemy.orm import aliased

import ckan.plugins.toolkit as tk
import ckanext.hdx_user_extra.model as ue_model

_mail_recipient = tk.mail_recipient
_render = tk.render
_url_for = tk.url_for
config = tk.config


MAIL_TEXT_TEMPLATE = '''
Dear {full_name},\n
\n
We would like to remind you that you have an API token that is about to expire.\n
\n
Token: {token_name}\n
Expires: {expires}\n
Last access: {last_access}\n
\n
The times shown above are in UTC.\n
To manage your tokens go to {api_tokens_url} .\n
'''


def find_expiring_api_tokens(model, session, days_in_advance, expires_on_specified_day):
    '''
    :param model:
    :type model: ckan.model
    :param session:
    :type session: sqlalchemy.orm.scoped_session
    :param days_in_advance:
    :type days_in_advance: int
    :param expires_on_specified_day:
    :type expires_on_specified_day: bool
    :return:
    :rtype: tuple[list[dict], str, str]
    '''
    now = datetime.datetime.now()
    period_start = now
    if expires_on_specified_day:
        period_start = now + datetime.timedelta(days=days_in_advance)
    period_start_string = period_start.isoformat()[:10]

    period_end = now + datetime.timedelta(days=days_in_advance + 1)
    period_end_string = period_end.isoformat()[:10]

    first_name_alias = aliased(ue_model.UserExtra)
    last_name_alias = aliased(ue_model.UserExtra)
    query = session.query(model.ApiToken,
                          model.User,
                          first_name_alias.value,
                          last_name_alias.value) \
        .join(model.User, model.ApiToken.user_id == model.User.id) \
        .outerjoin(first_name_alias,
                   and_(model.User.id == first_name_alias.user_id, first_name_alias.key == 'hdx_first_name')
                   ) \
        .outerjoin(last_name_alias,
                   and_(model.User.id == last_name_alias.user_id, last_name_alias.key == 'hdx_last_name')
                   ) \
        .filter(model.ApiToken.plugin_extras['expire_api_token']['exp'].astext >= period_start_string,
                model.ApiToken.plugin_extras['expire_api_token']['exp'].astext < period_end_string)
    query_result = query.all()

    result = [
        {
            'token_name': token.name,
            'expires': __format_date_for_email(get_expiration(token)),
            'last_access': __format_date_for_email(token.last_access.isoformat()) if token.last_access else 'Never',
            'username': user.name,
            'email': user.email,
            'full_name': '{} {}'.format(first_name, last_name) if first_name and last_name else user.fullname,
            'api_tokens_url': _url_for('user.api_tokens', id=user.name, qualified=True)
        }
        for token, user, first_name, last_name in query_result
    ]
    return result, period_start_string, period_end_string


def __format_date_for_email(date_string):
    return date_string.replace('T', ' ')[:19]


def get_expiration(token):
    '''
    :param token:
    :type token: ckan.model.ApiToken
    :return:
    :rtype: str
    '''
    return token.plugin_extras['expire_api_token']['exp']


def send_emails_for_expiring_tokens(token_info_list):
    for token_info in token_info_list:
        rendered_text = MAIL_TEXT_TEMPLATE.format(**token_info)
        html_data_dict = {
            'data': {
                'data': token_info,
                'footer': True,
                '_snippet': 'email/content/api_tokens/api_token_expiration.html',
                'logo_hdx_email': config.get('ckan.site_url', '#') + '/images/homepage/logo-hdx-email.png',
            }
        }
        rendered_html = _render('email/email.html', html_data_dict)
        _mail_recipient(
            token_info.get('full_name'),
            token_info.get('email'),
            'HDX API Token Expiration Warning',
            rendered_text,
            body_html=rendered_html
        )

    return len(token_info_list) if token_info_list else 0
