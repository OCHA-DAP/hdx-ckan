import logging

from ckanext.hdx_theme.util.analytics import AbstractAnalyticsSender

log = logging.getLogger(__name__)


class APICallAnalyticsSender(AbstractAnalyticsSender):

    def __init__(self, action_name):
        super(APICallAnalyticsSender, self).__init__()

        self.analytics_dict = {
            'event_name': 'programmatic use',
            'mixpanel_meta': {
                'event source': 'api',
                'action name': action_name
            },
            'ga_meta': {
                'ec': 'api',  # event category
                'ea': action_name,  # event action
            }
        }

