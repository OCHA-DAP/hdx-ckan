COMMON_HEADER = '''
const BOT_STRINGS = ['bot', 'crawler', 'spider', 'hxl-proxy', 'hdxinternal', 'data\.world', 'opendataportalwatch', 'microsoft\ office', 'turnitin']
const regex = new RegExp(BOT_STRINGS.join('|'), 'i')
function containsAny(value) {{
  if (value) {{
    return regex.test(value)
  }}
}}
'''

COMMON_FILTER = '''
    .filter(event => event.properties['org name'] && event.properties['org name'] != 'None')
    .filter(event => event.properties['user agent'] != '' && !containsAny(event.properties['user agent']) && !containsAny(event.properties['$browser']))
'''

BOT_FILTER = '''
    .filter(event => event.properties['user agent'] != '' && !containsAny(event.properties['user agent']) && !containsAny(event.properties['$browser']))
'''

ORG_FILTER = '''
    .filter(event => event.properties['org name'] && event.properties['org name'] != 'None')
'''

DOWNLOADS_PER_DATASET = '''
/* 6. unique downloads by dataset
VER 1.3

ver 1.3 changed to use groupByUser() instead of 1st groupBy() and have the first reducer be null() - recommended by mixpanel support as being more performant.

used for total downloads from 2016-08-01 which is used to sort datasets by "most downloads" for the "XXX downloads" counter on /search and on each individual dataset

gets all download events and counts occurrences of unique combinations of user, resource, and dataset, and day, then counts the number of occurrences of dataset by week.  In other words, if a user downloaded all 3 resources on a dataset 2 different times on the same day (6 total downloads), the result of this query would be 3.  It answers the question "What is the total number of downloads of any resource on a given dataset, ignorning repeated downloads from the same user the same day?"
*/

''' + COMMON_HEADER + \
'''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  ''' + COMMON_FILTER + \
  '''
  .groupByUser(["properties.resource id","properties.dataset id",mixpanel.numeric_bucket('time',mixpanel.daily_time_buckets)],mixpanel.reducer.null())
  .groupBy(["key.2"], mixpanel.reducer.count())
    .map(function(r){{
    return {{
      dataset_id: r.key[0],
      value: r.value
    }};
  }});
}}
'''

PAGEVIEWS_PER_DATASET = '''
/* 7. total PVs by dataset
VER 1.1

ver 1.1 added a filter to only take into consideration "page views" that have a "dataset id" property set

used for the flame icon and for sorting by "trending"
gets all page view events and counts the occurrence of each unique dataset.  It answers the question "How many times has this dataset page been viewed ?"

Note:  as of 12-july-2017, this query fails (or at least doesn't return what is expected), because there are no dataset IDs being sent with the page view event.
*/

''' + COMMON_HEADER + \
'''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: 'page view', selector: 'properties["dataset id"]'}}]
  }})
  ''' + COMMON_FILTER + \
  '''
  .groupBy(["properties.dataset id"],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      dataset_id: r.key[0],
      value: r.value
    }};
  }});
}}
'''

DOWNLOADS_PER_DATASET_PER_WEEK = '''
/* 1. unique downloads by dataset by week
VER 1.3

ver 1.3 splitting datasets in groups (0123, 4567, 89ab, cdef), for smaller result sets
ver 1.2 removing sorting function as it's not needed
ver 1.1 changed to use groupByUser() instead of 1st groupBy() and have the first reducer be null() - recommended by mixpanel support as being more performant.

unique (by distinct id, resource id, and day) # of downloads by dataset by week (last 24 weeks, used in timeline on dataset page)

selects all download events, counts unique combinations of user, resource, dataset and day, then counts the number of those unique combinations by dataset and week.
*/

''' + COMMON_HEADER + \
'''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  ''' + COMMON_FILTER + \
  '''
  .filter(function(event){{
    var first_letter = event.properties['dataset id'][0];
    return '{}'.includes(first_letter);
  }})
  .groupByUser(["properties.resource id","properties.dataset id",mixpanel.numeric_bucket('time',mixpanel.daily_time_buckets)],mixpanel.reducer.null())
  .groupBy(["key.2",(mixpanel.numeric_bucket('key.3',mixpanel.weekly_time_buckets))],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      dataset_id: r.key[0],
      date: new Date(r.key[1]).toISOString().substring(0,10),
      value: r.value
    }};
  }});
}}
'''

PAGEVIEWS_PER_ORGANIZATION = '''
/* 2. unique PVs by organization
VER 1.1

ver 1.1 changed to use groupByUser() instead of 1st groupBy() and have the first reducer be null() - recommended by mixpanel support as being more performant. Also added a filter to only take into consideration "page views" that have an "org id" property set

used for unique visitors key figure on org stats page
gets all page view events and counts unique combinations of user and org.  This is to say, if a single user looked at 3 different datasets from a single organization and then looked at the organization page as well (4 total page views), the count returned by this query would be 1.  It answers the question "How many individuals looked at one or more of an organization's content within a given time period."
*/

''' + COMMON_HEADER + \
'''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: 'page view', selector: 'properties["org id"]'}}]
  }})
  ''' + COMMON_FILTER + \
  '''
  .groupByUser(['properties.org id'],mixpanel.reducer.null())
  .groupBy([function(row) {{return row.key.slice(1)}}],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      org_id: r.key[0],
      value: r.value
    }};
  }});
}}
'''

DOWNLOADS_PER_ORGANIZATION = '''
/* 3. unique downloads by organization
VER 1.1

ver 1.1 changed to use groupByUser() instead of 1st groupBy() and have the first reducer be null() - recommended by mixpanel support as being more performant.

used as "unique downloaders" key figure on org page
gets all download events and counts unique combinations of user and org.  This is to say, if a single user downloaded 5 resources 2 times from datasets belonging to a given organization (10 total downloads), the count returned by this query would be 1.  It answers the question "How many individuals downloaded one or more resources from an organization's datasets."
*/

''' + COMMON_HEADER + \
'''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  ''' + COMMON_FILTER + \
  '''
  .groupByUser(["properties.org id"],mixpanel.reducer.null())
  .groupBy([function(row) {{return row.key.slice(1)}}],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      org_id: r.key[0],
      value: r.value
    }};
  }});
}}
'''

PAGEVIEWS_PER_ORGANIZATION_PER_WEEK = '''
/* 4. total PVs by org by week
VER 1.1

ver 1.1 changing selector to also filter null 'org ids'. Removing sorting as it is not needed.

used as timeline on org page
gets all page view events and counts unique combinations of week and org.  It answers the question "How many page views did an organization's content receive in a given week."
*/

''' + COMMON_HEADER + \
'''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: 'page view', selector: 'properties["org id"]'}}]
  }})
  ''' + COMMON_FILTER + \
  '''
  .groupBy(['properties.org id',mixpanel.numeric_bucket('time',mixpanel.weekly_time_buckets)],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      org_id: r.key[0],
      date: new Date(r.key[1]).toISOString().substring(0,10),
      value: r.value
    }};
  }});
}}
'''

DOWNLOADS_PER_ORGANIZATION_PER_WEEK = '''
/* 5. unique downloads by org by week
VER 1.2

ver 1.2 removing sorting function as it's not needed
ver 1.1 changed to use groupByUser() instead of 1st groupBy() and have the first reducer be null() - recommended by mixpanel support as being more performant.

used in timeline on org page
selects all download events, counts unique combinations of user, resource, and org, then counts the number of those unique combinations by org by week.  For each week, it gives the total number of times a resource was downloaded from an organization, excluding multiple downloads of the same resource by the same users on the same day.
*/

''' + COMMON_HEADER + \
'''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  ''' + COMMON_FILTER + \
  '''
  .groupByUser(["properties.resource id","properties.org id",mixpanel.numeric_bucket('time',mixpanel.daily_time_buckets)],mixpanel.reducer.null())
  .groupBy(["key.2",(mixpanel.numeric_bucket('key.3',mixpanel.weekly_time_buckets))],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      org_id: r.key[0],
      date: new Date(r.key[1]).toISOString().substring(0,10),
      value: r.value
    }};
  }});
}}
'''

DOWNLOADS_PER_ORGANIZATION_PER_DATASET = '''
/* 8. unique downloads by dataset by organization
VER 1.1

ver 1.2 removing sorting from the query, we can do the sorting in HDX - recommended by MP support
ver 1.1 changed to use groupByUser() instead of 1st groupBy() and have the first reducer be null() - recommended by mixpanel support as being more performant. Also simplified second groupBy() to use "key.X" instead of function call
ver 1.0 changed to bucket by day to be consistent with definition of uniqueness for similar queries

Used for top downloads bar chart on org page for last 24 weeks
selects all download events, counts unique combinations of user, resource, day, dataset, and org, then counts the number of those unique combinations by dataset.  That is to say if a single user downloaded 10 different resources two times each (20 total downloads) from a single dataset in a given day (and on no other days), the count returned by this query would be 10
*/

''' + COMMON_HEADER + \
'''
function main() {{
  return Events({{
    from_date: "{}",
    to_date: "{}",
    event_selectors: [{{event: "resource download"}}]
  }})
  ''' + COMMON_FILTER + \
  '''
  .groupByUser(["properties.resource id",mixpanel.numeric_bucket("time",mixpanel.daily_time_buckets),"properties.dataset id", "properties.org id"],mixpanel.reducer.null())
  .groupBy(["key.4", "key.3"],mixpanel.reducer.count())
  .map(function(r){{
    return {{
    org_id: r.key[0],
    dataset_id: r.key[1],
    value: r.value
    }};
  }});
}}
'''
