import logging

from ckanext.hdx_theme.util.analytics_api import APICallAnalyticsSender

log = logging.getLogger(__name__)

class APITrackingMiddleware(object):
    def __init__(self, app, config):
        self.app = app

    def __call__(self, environ, start_response):
        app = self.app(environ, start_response)

        routing_args = environ.get('wsgiorg.routing_args')
        route_info = routing_args[1] if routing_args and len(routing_args) > 1 else {}

        if (route_info.get('controller') == 'api'):
            log.debug('API Call: ' + str(route_info))
            logic_function = route_info.get('logic_function')
            api_action = logic_function if logic_function else route_info.get('action')
            log.debug('Action:'+ api_action)
            APICallAnalyticsSender(api_action).send_to_queue()

        return app