import logging
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)
request = tk.request

NOT_ALLOWED_FLASK_ROUTES = {'/<path:filename>', '/global/<filename>', '/webassets/<path:path>', '/api/i18n/<lang>'}


class CookieMiddleware(object):

    def __init__(self, app, config):
        self.app = app
        self.config = config

    def __call__(self, environ, start_response):
        flask_route = environ.get('HDXflask_route')
        pylons_route = environ.get('HDXpylons_route')
        ckan_app = environ.get('ckan.app', 'flask_app')
        if (ckan_app == 'flask_app' and flask_route in NOT_ALLOWED_FLASK_ROUTES) or \
            (ckan_app == 'pylons_app' and not pylons_route):
            environ.get('beaker.session')._headers['cookie_out'] = None
        else:
            log.info('Allowing set cookie for: ' + environ.get('CKAN_CURRENT_URL'))
        app = self.app(environ, start_response)
        return app


