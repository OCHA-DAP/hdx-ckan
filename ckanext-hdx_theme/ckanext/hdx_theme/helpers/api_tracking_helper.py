import logging

from user_agents import parse

try:
    # CKAN 2.7 and later
    from ckan.common import config
except ImportError:
    # CKAN 2.6 and earlier
    from pylons import config

log = logging.getLogger(__name__)


def is_api_call(environ):
    route_info = get_route_info(environ)

    if (route_info.get('controller') == 'api'):
        user_agent_str = environ.get('HTTP_USER_AGENT')
        user_agent = parse(user_agent_str)

        exclude_browsers_string = config.get('hdx.analytics.track_api.exclude_browsers')
        exclude_browsers = exclude_browsers_string.split(',')
        if any(item in user_agent.browser.family for item in exclude_browsers):
            return False

        exclude_other_string = config.get('hdx.analytics.track_api.exclude_other')
        exclude_other = exclude_other_string.split(',')
        if any(item in user_agent_str for item in exclude_other):
            return False

        return True

    return False


def get_route_info(environ):
    routing_args = environ.get('wsgiorg.routing_args')
    return routing_args[1] if routing_args and len(routing_args) > 1 else {}


def get_api_action(environ):
    route_info = get_route_info(environ)
    logic_function = route_info.get('logic_function')
    return logic_function if logic_function else route_info.get('action')
