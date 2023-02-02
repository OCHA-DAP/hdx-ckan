import ckan.model as model
import ckan.plugins.toolkit as tk

from datetime import datetime

_get_action = tk.get_action
_url_for = tk.url_for
_render = tk.render
_mail_recipient = tk.mail_recipient
config = tk.config
NotFound = tk.ObjectNotFound


MAIL_TEXT_TEMPLATE = '''
Dear {full_name},\n
A new API token has been created for your HDX account.\n
If you created the token then you can disregard this email.\n
Otherwise, it's possible that someone else has access to your HDX account. In this case you should: \n
  1) change the password of your HDX account \n
  2) revoke all your API tokens and then create new ones, {api_tokens_url} \n
  3) let us know about this issue at hdx@humdata.org \n
\n
Token details: \n
  - Token Name: {token_name} \n
  - Expires: {expires} (UTC) \n
\n
To manage your tokens go to {api_tokens_url} .\n
'''


def send_email_on_token_creation(username, token_name, expiration_in_millis):
    full_name, email = _get_user_full_name_and_email(username)

    isodate = datetime.fromtimestamp(expiration_in_millis).isoformat()

    api_tokens_url = _url_for('user.api_tokens', id=username, qualified=True)

    token_info = {
        'full_name': full_name,
        'token_name': token_name,
        'expires': isodate,
        'api_tokens_url': api_tokens_url,
    }

    rendered_text = MAIL_TEXT_TEMPLATE.format(**token_info)

    html_data_dict = {
        'data': {
            'data': token_info,
            'footer': True,
            '_snippet': 'email/content/api_tokens/api_token_creation.html',
            'logo_hdx_email': config.get('ckan.site_url', '#') + '/images/homepage/logo-hdx-email.png',
        }
    }
    rendered_html = _render('email/email.html', html_data_dict)
    _mail_recipient(
        full_name,
        email,
        'Security Notification: HDX API Token Created',
        rendered_text,
        body_html=rendered_html
    )


def _get_user_full_name_and_email(username):
    context = {
        'model': model,
        'session': model.Session,
        'user': username,
        'ignore_auth': True
    }
    user_dict = _get_action('user_show')(context, {'id': username})
    if not user_dict:
        raise NotFound('No user data found for username: {}'.format(username))
    if '@' not in user_dict.get('email', ''):
        raise NotFound('No email address found for username: {}'.format(username))
    firstname = user_dict.get('firstname')
    lastname = user_dict.get('lastname')
    if firstname and lastname:
        full_name = '{} {}'.format(firstname, lastname)
    else:
        full_name = user_dict.get('fullname') or user_dict.get('name')

    return full_name, user_dict.get('email')
