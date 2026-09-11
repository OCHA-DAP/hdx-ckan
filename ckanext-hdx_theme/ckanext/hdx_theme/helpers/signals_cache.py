import logging

from dogpile.cache import make_region

from ckanext.hdx_theme.helpers.caching import (
    dogpile_config_filter,
    dogpile_standard_config,
    HDXRedisInvalidationStrategy,
    cache_only_if_truthy_wrapper,
)

log = logging.getLogger(__name__)

_dogpile_signals_config = {
    **dogpile_standard_config,
    'cache.redis.expiration_time': 60 * 10,
    'cache.local.expiration_time': 60 * 10,
}

dogpile_signals_region = make_region(key_mangler=lambda key: 'signals-' + key)
dogpile_signals_region.configure_from_config(_dogpile_signals_config, dogpile_config_filter)

if dogpile_config_filter == 'cache.redis.':
    dogpile_signals_region.region_invalidator = HDXRedisInvalidationStrategy(dogpile_signals_region)


@cache_only_if_truthy_wrapper(dogpile_signals_region)
def cached_last_three_signal_cards():
    from ckanext.hdx_theme.helpers.helpers import hdx_fetch_last_three_signal_cards
    return hdx_fetch_last_three_signal_cards()
