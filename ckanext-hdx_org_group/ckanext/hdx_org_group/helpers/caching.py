import logging
from dogpile.cache import make_region

import ckan.plugins.toolkit as tk
import ckanext.hdx_org_group.helpers.data_completness as data_completness
from ckanext.hdx_theme.helpers.caching import dogpile_standard_config, dogpile_config_filter, \
    HDXRedisInvalidationStrategy

log = logging.getLogger(__name__)
config = tk.config

dogpile_config = {
    'cache.redis.expiration_time': 60 * 60,
}
dogpile_config.update(dogpile_standard_config)

dogpile_country_region = make_region(key_mangler=lambda key: 'country-' + key)
dogpile_country_region.configure_from_config(dogpile_config, dogpile_config_filter)

if dogpile_config_filter == 'cache.redis.':
    dogpile_country_region.region_invalidator = HDXRedisInvalidationStrategy(dogpile_country_region)


@dogpile_country_region.cache_on_arguments()
def cached_data_completeness(location_code):
    log.info('Fetching data completness for ' + location_code)
    url_pattern = config.get('hdx.datagrid.config_url_pattern')
    for_prod = config.get('hdx.datagrid.prod') == 'true'
    branch = 'master' if for_prod else location_code
    url = url_pattern.format(branch=branch, iso=location_code)

    return data_completness.DataCompletness(location_code, url).get_config()


@dogpile_country_region.cache_on_arguments()
def cached_topline_numbers(id, activity_level=None):
    '''
    :param id:
    :type id: string
    :param activity_level: used to invalidate cache for one group (activity_level) - relief web
    :type activity_level: string

    :return: list with topline numbers for a group
    :rtype: list
    '''
    return tk.get_action('hdx_topline_num_for_group')({}, {'id': id, 'common_format': 'false'})
