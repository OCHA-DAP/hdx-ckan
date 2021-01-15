import logging

log = logging.getLogger(__name__)


class RedirectionMiddleware(object):
    @staticmethod
    def __check_redirect(path):
        if path:
            if path.endswith('group/'):
                return '/group'
            elif 'organization/?' in path:
                return path.replace('organization/?', 'organization?')
        return None

    def __init__(self, app, config):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ.get('CKAN_CURRENT_URL')
        new_path = self.__check_redirect(path)
        if new_path:
            start_response('302 Found', [('Location', new_path)])
            return ['1']
        app = self.app(environ, start_response)
        return app
