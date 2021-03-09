import logging

from six.moves.urllib.parse import unquote


log = logging.getLogger(__name__)


class RedirectionMiddleware(object):
    @staticmethod
    def __check_redirect(path):
        if path:
            if path.endswith('/'):
                return path[:-1]
            elif '/?' in path:
                return path.replace('/?', '?')
        return None

    def __init__(self, app, config):
        self.app = app

    def __call__(self, environ, start_response):
        path = environ.get('CKAN_CURRENT_URL')
        new_path = self.__check_redirect(path)
        if new_path:
            new_path = unquote(new_path)
            start_response('302 Found', [('Location', new_path)])
            return ['1']
        app = self.app(environ, start_response)
        return app
