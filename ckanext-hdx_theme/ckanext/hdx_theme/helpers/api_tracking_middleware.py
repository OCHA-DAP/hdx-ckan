import logging

from ckanext.hdx_theme.util.analytics_api import APICallAnalyticsSender

import api_tracking_helper as api_th

log = logging.getLogger(__name__)

class APITrackingMiddleware(object):
    def __init__(self, app, config):
        self.app = app

    def __call__(self, environ, start_response):
        app = self.app(environ, start_response)


        if (api_th.is_api_call(environ)):
            route_info = api_th.get_route_info(environ)
            log.debug('API Call: ' + str(route_info))
            api_action = api_th.get_api_action(environ)
            log.debug('Action:' + api_action)
            APICallAnalyticsSender(api_action).send_to_queue()

        return app
