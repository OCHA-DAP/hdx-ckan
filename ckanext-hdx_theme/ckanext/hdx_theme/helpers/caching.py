import logging
import requests
import pylons.config as config
from dogpile.cache import make_region

log = logging.getLogger(__name__)

dogpile_config_filter = 'cache.redis.' if config.get('hdx.caching.use_redis') == 'true' else 'cache.local.'
dogpile_standard_config = {
    'cache.local.backend': 'dogpile.cache.dbm',
    'cache.local.arguments.filename': config.get('hdx.caching.dogpile_filename', '/tmp/hdx_dogpile_cache.dbm'),
    'cache.local.expiration_time': 60 * 60 * 1,

    'cache.redis.backend': 'dogpile.cache.redis',
    'cache.redis.arguments.host': config.get('hdx.caching.redis_host', 'gisredis') or 'gisredis',
    'cache.redis.arguments.port': int(config.get('hdx.caching.redis_port', '6379') or 6379),
    'cache.redis.arguments.db': int(config.get('hdx.caching.redis_db', '3') or 3),
    'cache.redis.arguments.redis_expiration_time': 60 * 60 * 24 * 3,  # 3 days - higher than the expiration time
    'cache.redis.arguments.distributed_lock': True
}
dogpile_config = {
    'cache.redis.expiration_time': 60 * 60 * 24,
}
dogpile_config.update(dogpile_standard_config)

dogpile_requests_region = make_region(key_mangler=lambda key: 'requests-' + key)

dogpile_requests_region.configure_from_config(dogpile_config, dogpile_config_filter)


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
