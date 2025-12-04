import logging

import ckan.model as model
import ckan.plugins.toolkit as tk

from datetime import datetime

_get_action = tk.get_action
_url_for = tk.url_for
_render = tk.render
_mail_recipient = tk.mail_recipient
config = tk.config
NotFound = tk.ObjectNotFound

log = logging.getLogger(__name__)


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
    if config.get('hdx.api_token.email_notifications.enabled') is False:
        log.warning('API token email notifications are disabled')
        return

    # Check if we have Flask application context (required for template rendering)
    # If not (e.g., CLI command), create one temporarily
    needs_app_context = False
    try:
        from flask import has_app_context
        if not has_app_context():
            needs_app_context = True
            log.debug('No Flask app context detected - creating temporary context for email rendering')
    except (ImportError, RuntimeError):
        log.error('Flask not available - cannot send email notification')
        return

    # Get Flask app and create context if needed
    app_context = None
    request_context = None
    if needs_app_context:
        try:
            import ckan.config.middleware as middleware
            wsgi_app = middleware.make_app(config)
            # The actual Flask app is wrapped in middleware, access it via _wsgi_app
            flask_app = wsgi_app._wsgi_app
            # Create both app context and request context (needed for session/render)
            app_context = flask_app.app_context()
            app_context.push()
            request_context = flask_app.test_request_context()
            request_context.push()
        except Exception as e:
            log.error(f'Failed to create Flask contexts: {e}')
            return

    try:
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
                'logo_hdx_email': config.get('ckan.site_url', '#') + '/images/homepage/logo-hdx.png',
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
    finally:
        # Clean up contexts if we created them (in reverse order)
        if request_context:
            request_context.pop()
        if app_context:
            app_context.pop()


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
    fullname = user_dict.get('fullname')

    return fullname, user_dict.get('email')
