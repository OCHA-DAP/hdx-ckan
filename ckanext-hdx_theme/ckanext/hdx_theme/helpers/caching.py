import logging
from functools import wraps

import requests
import time
# import datetime
# import dateutil.parser

from dogpile.cache import make_region
from dogpile.cache.api import NO_VALUE
from dogpile.cache.region import RegionInvalidationStrategy, CacheRegion

from redis import StrictRedis

import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)
config = tk.config

dogpile_config_filter = 'cache.redis.' if config.get('hdx.caching.use_redis') else 'cache.local.'
dogpile_standard_config = {
    'cache.local.backend': 'dogpile.cache.dbm',
    'cache.local.arguments.filename': config.get('hdx.caching.dogpile_filename', '/tmp/hdx_dogpile_cache.dbm'),
    'cache.local.expiration_time': 60 * 60 * 1,

    'cache.redis.backend': 'dogpile.cache.redis',
    'cache.redis.arguments.host': config.get('hdx.caching.redis_host'),
    'cache.redis.arguments.port': config.get('hdx.caching.redis_port'),
    'cache.redis.arguments.db': config.get('hdx.caching.redis_db'),
    'cache.redis.arguments.redis_expiration_time': 60 * 60 * 24 * 3,  # 3 days - higher than the expiration time
    'cache.redis.arguments.distributed_lock': True,
    'cache.redis.arguments.lock_timeout': 60 * 2,  # 2 mins
}
dogpile_config = {
    'cache.redis.expiration_time': 60 * 60 * 24,
}
dogpile_config.update(dogpile_standard_config)

dogpile_requests_region = make_region(key_mangler=lambda key: 'requests-' + key)
dogpile_requests_region.configure_from_config(dogpile_config, dogpile_config_filter)


class HDXRedisInvalidationStrategy(RegionInvalidationStrategy):

    def __init__(self, dogpile_region):
        '''

        :param dogpile_region:
        :type dogpile_region: CacheRegion
        '''
        self.dogpile_region = dogpile_region

    def invalidate(self, hard=None):
        mangler, redis = self._find_backend_info()
        # time = datetime.datetime.utcnow().isoformat()
        current_time = time.time()
        type = 'hard' if hard else 'soft'
        key = self._create_key(mangler)
        value = type + '__' + str(current_time)

        redis.set(key, value)

    @classmethod
    def _create_key(self, mangler):
        '''
        :param mangler:
        :type mangler: (str) -> str
        :return:
        :rtype: str
        '''
        key = mangler('invalidate_key') if mangler else 'default-invalidate_key'
        return key

    def _find_backend_info(self):
        '''
        :return:
        :rtype: ((str) -> str, StrictRedis)
        '''
        mangler = self.dogpile_region.key_mangler  # type: str
        redis = self.dogpile_region.backend.writer_client  # type: StrictRedis
        return mangler, redis

    def _get_invalidation_info(self):
        mangler, redis = self._find_backend_info()
        key = self._create_key(mangler)

        value = redis.get(key)
        if isinstance(value, bytes):
            value = value.decode('utf-8')

        if value:
            parts = value.split('__')
            if len(parts) == 2:
                hard = True if parts[0] == 'hard' else False
                # time = dateutil.parser.parse(parts[1])
                current_time = float(parts[1])
                return hard, current_time

        return False, None

    def is_invalidated(self, timestamp):
        hard, invalidation_timestamp = self._get_invalidation_info()
        if invalidation_timestamp:
            return timestamp < invalidation_timestamp

        return False

    def was_hard_invalidated(self):
        hard, invalidation_timestamp = self._get_invalidation_info()
        if invalidation_timestamp:
            return hard
        return False

    def is_hard_invalidated(self, timestamp):
        hard, invalidation_timestamp = self._get_invalidation_info()
        if hard and invalidation_timestamp:
            return timestamp < invalidation_timestamp

        return False

    def was_soft_invalidated(self):
        hard, invalidation_timestamp = self._get_invalidation_info()
        if invalidation_timestamp:
            return not hard
        return False

    def is_soft_invalidated(self, timestamp):
        hard, invalidation_timestamp = self._get_invalidation_info()
        if not hard and invalidation_timestamp:
            return timestamp < invalidation_timestamp

        return False


if dogpile_config_filter == 'cache.redis.':
    dogpile_requests_region.region_invalidator = HDXRedisInvalidationStrategy(dogpile_requests_region)


@dogpile_requests_region.cache_on_arguments()
def cached_make_rest_api_request(url):
    '''
    Makes a GET response and expect a JSON response
    :param url:
    :type url: str
    :return: json transformed into a dict
    :rtype: dict
    '''
    log.info('Requesting indicators:' + url)

    response = requests.get(url)

    response.raise_for_status()

    return response.json()

def cache_only_if_truthy_wrapper(region: CacheRegion, *args, **kwargs):
    # Custom key generator wrapper to enforce the same namespace
    def _keygen(namespace, fn):
        # The `namespace` argument is required by dogpile's interface,
        # but unused here because we enforce our own namespace.
        return region.function_key_generator('only_truthy_values', fn)

    original_decorator = region.cache_on_arguments(
        function_key_generator=_keygen, *args, **kwargs
    )

    def decorator(f):
        cached_func = original_decorator(f)

        @wraps(f)
        def wrapper(*fn_args, **fn_kwargs):
            key_generator = _keygen(None, f)
            key = key_generator(*fn_args, **fn_kwargs)

            cached_value = region.get(key)
            if cached_value is not NO_VALUE:
                return cached_value
            # Call the original function
            result = f(*fn_args, **fn_kwargs)

            # Cache the result only if it's truthy
            if result:
                log.info(f'Caching result for key "{key}"')
                region.set(key, result)
            else:
                log.warning(f'Not caching result for key "{key}" because returned value was: {result}')

            return result

        wrapper.invalidate = cached_func.invalidate

        return wrapper

    return decorator


_SIGNALS_CACHE_KEY = 'signals_data:last_three_cards'
_SIGNALS_CACHE_TTL = 60 * 10


def cached_last_three_signal_cards():
    from ckanext.hdx_theme.helpers.helpers import hdx_fetch_last_three_signal_cards

    cached = dogpile_requests_region.get(_SIGNALS_CACHE_KEY, expiration_time=_SIGNALS_CACHE_TTL)
    if cached is not NO_VALUE:
        return cached

    try:
        result = hdx_fetch_last_three_signal_cards()
    except Exception as e:
        log.error(f'Failed to refresh HDX Signals cards: {e}')
        result = None

    if result:
        log.info('Creating cache for last three HDX Signals cards')
        dogpile_requests_region.set(_SIGNALS_CACHE_KEY, result)
        return result

    stale = dogpile_requests_region.get(_SIGNALS_CACHE_KEY, ignore_expiration=True)
    if stale is not NO_VALUE:
        log.warning('Serving stale HDX Signals cards after failed refresh')
        return stale

    return []
