import logging
import requests
import pylons.config as config
from dogpile.cache import make_region


log = logging.getLogger(__name__)

dogpile_requests_region = make_region(key_mangler=lambda key: 'requests-' + key)\
    .configure(
        'dogpile.cache.redis',
        expiration_time=60 * 60 * 24,
        arguments={
            'host': config.get('hdx.caching.redis_host', 'gisredis'),
            'port': int(config.get('hdx.caching.redis_port', '6379')),
            'db': int(config.get('hdx.caching.redis_db', '3')),
            'redis_expiration_time': 60 * 60 * 24 * 3,  # 3 days - we make sure it's higher than the expiration time
            'distributed_lock': True
        }
    )


@dogpile_requests_region.cache_on_arguments()
def cached_make_rest_api_request(url):
    '''
    Makes a GET response and expect a JSON response
    :param url:
    :type url: str
    :return: json transformed into a dict
    :rtype: dict
    '''
    log.info("Requesting indicators:" + url)

    response = requests.get(url)

    response.raise_for_status()

    return response.json()
