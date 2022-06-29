import collections
from ckanext.hdx_theme.util.analytics import AbstractAnalyticsSender


HDXStats = collections.namedtuple('HDXStats', [
    'datasets_total',
    'datasets_in_qa',
    'datasets_qa_completed',
    'datasets_with_quarantine',
    'datasets_with_no_quarantine',
    'orgs_total',
    'orgs_with_datasets',
    'orgs_active_last_year',
])


class HDXStatsAnalyticsSender(AbstractAnalyticsSender):
    def __init__(self, stats_helper):
        '''
        :param stats_helper:
        :type stats_helper: ckanext.hdx_theme.helpers.hdx_stats.HDXStatsHelper
        '''
        super(HDXStatsAnalyticsSender, self).__init__()

        mixpanel_meta = {
            'datasets total': stats_helper.datasets_total,
            'datasets in qa': stats_helper.datasets_qa_in_qa,
            'datasets qa completed': stats_helper.datasets_qa_qa_completed,
            'datasets with quarantine': stats_helper.datasets_qa_in_quarantine,
            'datasets with no quarantine': stats_helper.datasets_total - stats_helper.datasets_qa_in_quarantine,
            'orgs total': stats_helper.orgs_total,
            'orgs with datasets': stats_helper.orgs_with_datasets,
            'orgs updating data in past year': stats_helper.orgs_updating_data_past_year,
        }
        event_name = 'hdx stats'

        self.stats_dict = {
            'event_name': event_name,
            'mixpanel_meta': mixpanel_meta,
        }

        self.analytics_dict = {
            'event_name': event_name,
            'mixpanel_meta': dict(mixpanel_meta),
            'ga_meta': {}
        }
