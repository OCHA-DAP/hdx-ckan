import logging

from user_agents import parse

from ckan.common import config, request
from ckanext.hdx_theme.util.analytics import AbstractAnalyticsSender

log = logging.getLogger(__name__)


def send_api_analytics():
    api_tracking_enabled = config.get('hdx.analytics.track_api', 'false')
    if api_tracking_enabled:
        environ = request.environ
        if APICallAnalyticsSender._should_send_analytics_event(environ):
            action_name = APICallAnalyticsSender._get_api_action(environ)
            if action_name:
                _send_to_queue(action_name)


def _send_to_queue(action_name):
    APICallAnalyticsSender(action_name).send_to_queue()


class APICallAnalyticsSender(AbstractAnalyticsSender):

    def __init__(self, action_name):
        super(APICallAnalyticsSender, self).__init__()

        self.analytics_dict = {
            'event_name': 'robot api call',
            'mixpanel_meta': {
                'event source': 'api',
                'action name': action_name
            },
            'ga_meta': {
                'ec': 'api',  # event category
                'ea': action_name,  # event action
            }
        }

    @staticmethod
    def _should_send_analytics_event(environ):
        current_path = APICallAnalyticsSender._get_current_path(environ)
        # we're only interested in action API calls
        if '/action/' in current_path:
            user_agent_str = environ.get('HTTP_USER_AGENT')

            # no user_agent, we track the request
            if user_agent_str:
                try:
                    user_agent = parse(user_agent_str)

                    exclude_browsers_string = config.get('hdx.analytics.track_api.exclude_browsers')
                    if (exclude_browsers_string):
                        exclude_browsers = exclude_browsers_string.split(',')
                        if any(item in user_agent.browser.family for item in exclude_browsers):
                            return False
                except Exception as e:
                    log.error('Exception while trying to evaluate user_agent: %r', e)

                exclude_other_string = config.get('hdx.analytics.track_api.exclude_other')
                if exclude_other_string:
                    exclude_other = exclude_other_string.split(',')
                    if any(item in user_agent_str for item in exclude_other):
                        return False

            return True
        return False

    @staticmethod
    def _get_api_action(environ):
        url_path = APICallAnalyticsSender._get_current_path(environ)
        if url_path:
            parts = url_path.split('/')
            if len(parts) > 2:  # we should have at least 'action', 'api' and the action name as parts in the url path
                return parts[-1]
        return None

