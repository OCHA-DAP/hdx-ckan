import logging
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)
request = tk.request
g = tk.g

NOT_ALLOWED_FLASK_ROUTES = {'/<path:filename>', '/global/<filename>', '/webassets/<path:path>', '/api/i18n/<lang>'}

HDX_LOGGED_IN_COOKIE = 'hdx_logged_in'


def update_login_cookie(response):
    try:
        if request.url_rule and request.url_rule.rule not in NOT_ALLOWED_FLASK_ROUTES:
            new_cookie_value = None
            hdx_logged_in_cookie = int(request.cookies.get(HDX_LOGGED_IN_COOKIE, 0))
            logged_in = bool(g.user)
            if logged_in and not hdx_logged_in_cookie:
                new_cookie_value = "1"
            elif not logged_in and hdx_logged_in_cookie:
                new_cookie_value = "0"

            if new_cookie_value:
                response.set_cookie(HDX_LOGGED_IN_COOKIE, value=new_cookie_value, secure=True, httponly=True)
                log.info('Setting logged in cookie to {} for request {}'.format(new_cookie_value, request.path))
    except Exception as e:
        log.warning(str(e))

    return response


class CookieMiddleware(object):

    def __init__(self, app, config):
        self.app = app
        self.config = config

        # Run function after each request to potentially update the cookie that specifies whether the current user is
        # logged in
        if self.app.app_name == 'flask_app':
            self.app.after_request(update_login_cookie)

    def __call__(self, environ, start_response):
        flask_route = environ.get('HDXflask_route')
        pylons_route = environ.get('HDXpylons_route')
        ckan_app = environ.get('ckan.app', 'flask_app')

        if not flask_route and not pylons_route:
            # If running HDX on PY3 then HDXflask_route and HDXpylons_route won't be set because
            # AskAppDispatcherMiddleware is no longer used. CKANFlask is used directly.
            rule, args = self.app.url_map.bind_to_environ(environ).match(return_rule=True)
            flask_route = rule.rule
        if (ckan_app == 'flask_app' and flask_route in NOT_ALLOWED_FLASK_ROUTES) or \
            (ckan_app == 'pylons_app' and not pylons_route):
            environ.get('beaker.session')._headers['cookie_out'] = None
        else:
            log.info('Allowing set cookie for: ' + environ.get('CKAN_CURRENT_URL'))
        app = self.app(environ, start_response)
        return app


