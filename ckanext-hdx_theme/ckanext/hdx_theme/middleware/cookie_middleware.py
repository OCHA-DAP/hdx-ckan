import logging


log = logging.getLogger(__name__)


class CookieMiddleware(object):

    def __init__(self, app, config):
        self.app = app
        self.config = config

    def __call__(self, environ, start_response):
        if (environ['ckan.app'] == 'flask_app' and
                (environ['HDXflask_route'] == '/<path:filename>' or
                 environ['HDXflask_route'] == '/global/<filename>' or
                 environ['HDXflask_route'] == '/webassets/<path:path>')) or \
            (environ['ckan.app'] == 'pylons_app' and not environ['HDXpylons_route']):

            environ.get('beaker.session')._headers['cookie_out'] = None
        else:
            log.info('Allowing set cookie for: ' + environ.get('CKAN_CURRENT_URL'))
        app = self.app(environ, start_response)
        return app
