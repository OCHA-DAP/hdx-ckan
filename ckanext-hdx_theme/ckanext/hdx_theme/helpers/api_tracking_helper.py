import logging

log = logging.getLogger(__name__)

def is_api_call(environ):
    route_info = get_route_info(environ)

    if (route_info.get('controller') == 'api'):
        return True

    return False

def get_route_info(environ):
    routing_args = environ.get('wsgiorg.routing_args')
    return routing_args[1] if routing_args and len(routing_args) > 1 else {}

def get_api_action(environ):
    route_info = get_route_info(environ)
    logic_function = route_info.get('logic_function')
    return logic_function if logic_function else route_info.get('action')
