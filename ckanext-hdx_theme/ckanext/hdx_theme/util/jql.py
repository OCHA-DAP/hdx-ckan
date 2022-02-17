import requests
import logging

from dogpile.cache import make_region
from datetime import datetime, timedelta
from collections import OrderedDict
from functools import wraps

import ckan.plugins.toolkit as tk

import ckanext.hdx_theme.util.jql_queries as jql_queries
from ckanext.hdx_theme.util.timer import Timer
from ckanext.hdx_theme.helpers.caching import dogpile_standard_config, dogpile_config_filter, \
    HDXRedisInvalidationStrategy

config = tk.config

log = logging.getLogger(__name__)

dogpile_config = {
    'cache.redis.expiration_time': int(config.get('hdx.analytics.hours_for_results_in_cache', 24)) * 60 * 60,
}
dogpile_config.update(dogpile_standard_config)

dogpile_jql_region = make_region(key_mangler=lambda key: 'jql-' + key)
dogpile_jql_region.configure_from_config(dogpile_config, dogpile_config_filter)
if dogpile_config_filter == 'cache.redis.':
    dogpile_jql_region.region_invalidator = HDXRedisInvalidationStrategy(dogpile_jql_region)

CONFIG_API_SECRET = config.get('hdx.analytics.mixpanel.secret')
JQL_WARNING_THRESHOLD = int(config.get('hdx.analytics.mixpanel.warning_threshold_seconds', 90))

MIXPANEL_GROUPS = ['0123', '4567', '89ab', 'cdef']


class JqlQueryExecutor(object):
    def __init__(self, query):
        self.query = query
        self.args = []
        self.payload = None

    def run_query(self, transformer):
        self._compile_query()
        try:
            return self._run_query(transformer)
        except Exception as e:
            log.error('Ran into problems when getting data from mixpanel. Returning empty dict.')
            log.error(str(e))
            return {}

    def _compile_query(self):
        self.payload = {
            'script': self.query.format(*self.args)
        }

    def _run_query(self, transformer):
        '''
        :param transformer: transforms the request result
        :type transformer: MappingResultTransformer
        :return: a dict mapping the key to the values
        :rtype: dict
        '''
        nose_test = True if config.get('ckan.site_id') == 'test.ckan.net' else False
        if nose_test:
            return {}
        else:
            r = requests.post('https://mixpanel.com/api/2.0/jql', data=self.payload, auth=(CONFIG_API_SECRET, ''))
            r.raise_for_status()
            return transformer.transform(r)


class JqlQueryExecutorForHoursSinceNow(JqlQueryExecutor):
    def __init__(self, query, hours_since_now):
        super(JqlQueryExecutorForHoursSinceNow, self).__init__(query)
        self.args += self._compute_period(hours_since_now)

    @staticmethod
    def _compute_period(hours_since_now):
        '''
        :param hours_since_now: for how many hours back should the mixpanel call be made
        :type hours_since_now: int
        :return: a list with 2 iso date strings representing the beginning and ending of the period
        :rtype: list[str]
        '''
        until_date_str = datetime.utcnow().isoformat()[:10]

        from_date_str = (datetime.utcnow() - timedelta(hours=hours_since_now)).isoformat()[
                        :10] if hours_since_now else '2016-08-01'

        return [from_date_str, until_date_str]


class JqlQueryExecutorForWeeksSinceNow(JqlQueryExecutor):
    def __init__(self, query, weeks_since, since_date):
        '''
        :param query:
        :type query: str
        :param weeks_since:
        :type weeks_since: int
        :param since_date:
        :type since_date: datetime
        '''
        super(JqlQueryExecutorForWeeksSinceNow, self).__init__(query)
        self.args += self._compute_period(weeks_since, since_date)

    @staticmethod
    def _compute_period(weeks_since, since_date):
        '''
        :param weeks_since_now: for how many weeks back should the mixpanel call be made ( a week starts monday )
        :type weeks_since_now: int
        :param since_date:
        :type since_date: datetime
        :return: a list with 2 iso date strings representing the beginning and ending of the period
        :rtype: list[str]
        '''
        until_date = since_date
        until_date_str = until_date.isoformat()[:10]

        from_date = until_date - timedelta(weeks=weeks_since, days=until_date.weekday())
        from_date_str = from_date.isoformat()[:10]

        return [from_date_str, until_date_str]


class JqlQueryExecutorForWeeksSinceNowWithGroupFiltering(JqlQueryExecutorForWeeksSinceNow):
    def __init__(self, query, weeks_since, since_date, group):
        '''
        :param query:
        :type query: str
        :param weeks_since:
        :type weeks_since: int
        :param since_date:
        :type since_date: datetime
        :param group:
        :type group: MixpanelDatasetGroups
        '''
        super(JqlQueryExecutorForWeeksSinceNowWithGroupFiltering, self).__init__(query, weeks_since, since_date)
        self.args.append(group)


class MappingResultTransformer(object):
    def __init__(self, key_name):
        self.key_name = key_name

    def transform(self, response):
        '''

        :param response: the HTTP response
        :type response: requests.Response
        :return:
        :rtype: dict
        '''
        return {item.get(self.key_name): item.get('value') for item in response.json()}


class MultipleValueMappingResultTransformer(MappingResultTransformer):
    def __init__(self, key_name, secondary_key_name):
        super(MultipleValueMappingResultTransformer, self).__init__(key_name)
        self.secondary_key_name = secondary_key_name

    def transform(self, response):
        result = {}
        ''':type : dict[str, OrderedDict]'''

        for item in response.json():
            main_key = item.get(self.key_name)
            secondary_key = item.get(self.secondary_key_name)

            if main_key not in result:
                result[main_key] = OrderedDict()

            result[main_key][secondary_key] = {'value': item.get('value', 0), self.secondary_key_name: secondary_key}

        return result


class MultipleValueMandatoryMappingResultTransformer(MappingResultTransformer):
    def __init__(self, key_name, mandatory_key, mandatory_values):
        super(MultipleValueMandatoryMappingResultTransformer, self).__init__(key_name)
        self.mandatory_key = mandatory_key
        self.mandatory_values = mandatory_values

        self.template = [(item, {mandatory_key: item, 'value': 0}) for item in mandatory_values]

    def transform(self, response):
        result = {}
        ''':type : dict[str, OrderedDict]'''

        for item in response.json():
            main_key = item.get(self.key_name)
            secondary_key = item.get(self.mandatory_key)

            if secondary_key not in self.mandatory_values:
                log.error('{} not in mandatory values {}'.format(secondary_key, ','.join(self.mandatory_values)))
                continue

            if main_key not in result:
                result[main_key] = OrderedDict(self.template)

            result[main_key][secondary_key] = {'value': item.get('value', 0), self.mandatory_key: secondary_key}

        return result


def get_dataset_mp_group(dataset_id):
    first_letter = dataset_id[0]
    for group in MIXPANEL_GROUPS:
        if first_letter in group:
            return group
    log.error('Dataset group could not be determined for JQL query')
    return None


def timer_wrapper(original_caching_function):
    @wraps(original_caching_function)
    def timed_caching_function(*args):
        args_to_name = ', '.join(args)
        name = '{} with args ({})'.format(original_caching_function.__name__, args_to_name)
        timer = Timer(name,
                      init_message='creating cache',
                      in_millis=False, log_warning_step_threshold=JQL_WARNING_THRESHOLD)
        result = original_caching_function(*args)
        timer.next('finished')
        return result
    return timed_caching_function


@dogpile_jql_region.cache_on_arguments()
@timer_wrapper
def downloads_per_dataset_all_cached():
    return downloads_per_dataset()


def downloads_per_dataset(hours_since_now=None):
    query_executor = JqlQueryExecutorForHoursSinceNow(jql_queries.DOWNLOADS_PER_DATASET, hours_since_now)
    result = query_executor.run_query(MappingResultTransformer('dataset_id'))

    return result


def fetch_downloads_per_week_for_dataset(dataset_id):
    mixpanel_group = get_dataset_mp_group(dataset_id)
    if mixpanel_group:
        return downloads_per_dataset_per_week_last_24_weeks_cached(mixpanel_group).get(dataset_id, {})
    return {}


@dogpile_jql_region.cache_on_arguments()
@timer_wrapper
def downloads_per_dataset_per_week_last_24_weeks_cached(mixpanel_group):
    return downloads_per_dataset_per_week(mixpanel_group, 24)


def downloads_per_dataset_per_week(mixpanel_group, weeks=24):
    since = datetime.utcnow()
    query_executor = JqlQueryExecutorForWeeksSinceNowWithGroupFiltering(jql_queries.DOWNLOADS_PER_DATASET_PER_WEEK,
                                                                        weeks, since, mixpanel_group)

    mandatory_values = _generate_mandatory_dates(since, weeks)

    result = query_executor.run_query(
        MultipleValueMandatoryMappingResultTransformer('dataset_id', 'date', mandatory_values))

    return result


@dogpile_jql_region.cache_on_arguments()
@timer_wrapper
def downloads_per_organization_last_30_days_cached():
    return downloads_per_organization(30)


def downloads_per_organization(days_since_now=30):
    query_executor = JqlQueryExecutorForHoursSinceNow(jql_queries.DOWNLOADS_PER_ORGANIZATION, days_since_now * 24)
    result = query_executor.run_query(MappingResultTransformer('org_id'))

    return result


@dogpile_jql_region.cache_on_arguments()
@timer_wrapper
def downloads_per_organization_per_week_last_24_weeks_cached():
    return downloads_per_organization_per_week(24)


def downloads_per_organization_per_week(weeks=24):
    since = datetime.utcnow()
    query_executor = JqlQueryExecutorForWeeksSinceNow(jql_queries.DOWNLOADS_PER_ORGANIZATION_PER_WEEK, weeks, since)

    mandatory_values = _generate_mandatory_dates(since, weeks)

    result = query_executor.run_query(
        MultipleValueMandatoryMappingResultTransformer('org_id', 'date', mandatory_values))

    return result


@dogpile_jql_region.cache_on_arguments()
@timer_wrapper
def downloads_per_organization_per_dataset_last_24_weeks_cached():
    return downloads_per_organization_per_dataset(24)


def downloads_per_organization_per_dataset(weeks=24):
    since = datetime.utcnow()
    query_executor = JqlQueryExecutorForWeeksSinceNow(jql_queries.DOWNLOADS_PER_ORGANIZATION_PER_DATASET, weeks, since)

    result = query_executor.run_query(
        MultipleValueMappingResultTransformer('org_id', 'dataset_id'))

    return result


@dogpile_jql_region.cache_on_arguments()
@timer_wrapper
def pageviews_per_dataset_last_14_days_cached():
    hours = 14 * 24
    return pageviews_per_dataset(hours)


def pageviews_per_dataset(hours_since_now=None):
    query_executor = JqlQueryExecutorForHoursSinceNow(jql_queries.PAGEVIEWS_PER_DATASET, hours_since_now)
    result = query_executor.run_query(MappingResultTransformer('dataset_id'))

    return result


@dogpile_jql_region.cache_on_arguments()
@timer_wrapper
def pageviews_per_organization_last_30_days_cached():
    return pageviews_per_organization(30)


def pageviews_per_organization(days_since_now=30):
    query_executor = JqlQueryExecutorForHoursSinceNow(jql_queries.PAGEVIEWS_PER_ORGANIZATION, days_since_now * 24)
    result = query_executor.run_query(MappingResultTransformer('org_id'))

    return result


@dogpile_jql_region.cache_on_arguments()
@timer_wrapper
def pageviews_per_organization_per_week_last_24_weeks_cached():
    return pageviews_per_organization_per_week(24)


def pageviews_per_organization_per_week(weeks=24):
    since = datetime.utcnow()
    query_executor = JqlQueryExecutorForWeeksSinceNow(jql_queries.PAGEVIEWS_PER_ORGANIZATION_PER_WEEK, weeks, since)

    mandatory_values = _generate_mandatory_dates(since, weeks)

    result = query_executor.run_query(
        MultipleValueMandatoryMappingResultTransformer('org_id', 'date', mandatory_values))

    return result


def _generate_mandatory_dates(since, weeks):
    '''
    :param since: the datetime "until" object
    :type since: datetime
    :param weeks:
    :type weeks: int
    :return: list of mandatory dates
    :rtype: list[str]
    '''
    mandatory_dates = []

    ''':type : list[datetime]'''
    for i in range(0, weeks+1):
        mandatory_dates.insert(0, since - timedelta(weeks=i, days=since.weekday()))
    mandatory_values = list(map(lambda x: x.isoformat()[:10], mandatory_dates))
    return mandatory_values
