import requests
import beaker.cache as bcache
import pylons.config as config

from datetime import datetime, timedelta

import ckanext.hdx_theme.util.jql_queries as jql_queries

bcache.cache_regions.update({
    'hdx_jql_cache': {
        'expire': int(config.get('hdx.analytics.hours_for_results_in_cache', 24)) * 60 * 60,  # 1 days
        'type': 'file',
        'data_dir': '/tmp/hdx/jql_cache/data',
        'lock_dir': '/tmp/hdx/jql_cache/lock',
        'key_length': 250
    }
})

CONFIG_API_SECRET = config.get('hdx.analytics.mixpanel.secret')

# DOWNLOADS_PER_DATASET = 'function main(){{return Events({{from_date:"{}",to_date:"{}"}}).filter(function(e){{return"resource download"==e.name}}).groupBy(["properties.dataset id"],mixpanel.reducer.count()).sortDesc("value").map(function(e){{return{{dataset_id:e.key[0],value:e.value}}}})}}'


@bcache.cache_region('hdx_jql_cache', 'downloads_per_dataset')
def downloads_per_dataset_cached(hours=None):
    return downloads_per_dataset(hours)


def downloads_per_dataset(hours=None):
    until_date_str = datetime.utcnow().isoformat()[:10]

    from_date_str = (datetime.utcnow() - timedelta(hours=hours)).isoformat()[:10] if hours else '2016-08-01'

    payload = {
        'script': jql_queries.DOWNLOADS_PER_DATASET.format(from_date_str, until_date_str)
    }

    r = requests.post('https://mixpanel.com/api/2.0/jql', data=payload, auth=(CONFIG_API_SECRET, ''))
    r.raise_for_status()
    return {item.get('dataset_id'): item.get('value') for item in r.json()}