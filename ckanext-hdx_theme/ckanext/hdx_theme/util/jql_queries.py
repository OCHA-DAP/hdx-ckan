DOWNLOADS_PER_DATASET = '''
/* VER 1.2

used for total downloads from 2016-08-01 which is used to sort datasets by "most downloads" for the "XXX downloads" counter on /search and on each individual dataset

gets all download events and counts occurrences of unique combinations of user, resource, and dataset, and day, then counts the number of occurrences of dataset by week.  In other words, if a user downloaded all 3 resources on a dataset 2 different times on the same day (6 total downloads), the result of this query would be 3.  It answers the question "What is the total number of downloads of any resource on a given dataset, ignorning repeated downloads from the same user the same day?"*/

function main() {{
  return Events({{
    from_date: '2016-08-01',
    to_date: '2017-08-09',
    event_selectors: [{{event: "resource download"}}]
  }})
  .groupBy(["distinct_id","properties.resource id","properties.dataset id",mixpanel.numeric_bucket('time',mixpanel.daily_time_buckets)],mixpanel.reducer.count())
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
/* VER 1.0
gets all page view events and counts the occurrence of each unique dataset.  It answers the question "How many times has this dataset page been viewed?"*/

/* Note:  as of 12-july-2017, this query fails (or at least doesn't return what is expected), because there are no dataset IDs being sent with the page view event.*/

function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "page view"}}]
  }})
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
/* VER 1.0
selects all download events, counts unique combinations of week, user, resource, and dataset, then counts the number of those unique combinations by dataset.  That is to say if a single user downloaded 10 different resources two times each (20 total downloads) from a single dataset in a given week, the count returned by this query would be 10*/

function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  .groupBy(["distinct_id","properties.resource id","properties.dataset id",mixpanel.numeric_bucket('time',mixpanel.daily_time_buckets)],mixpanel.reducer.count())
  .groupBy(["key.2",(mixpanel.numeric_bucket('key.3',mixpanel.weekly_time_buckets))],mixpanel.reducer.count())
  .sortAsc(function(row){{return row.key[1]}})
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
/* VER 1.0
gets all page view events and counts unique combinations of user and org.  This is to say, if a single user looked at 3 different datasets from a single organization and then looked at the organization page as well (4 total page views), the count returned by this query would be 1.  It answers the question "How many individuals looked at one or more of an organization's content."*/

function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "page view"}}]
  }})
  .groupBy(["distinct_id","properties.org id"],mixpanel.reducer.count())
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
/* VER 1.0
gets all download events and counts unique combinations of user and org.  This is to say, if a single user downloaded 5 resources 2 times from datasets belonging to a given organization (10 total downloads), the count returned by this query would be 1.  It answers the question "How many individuals one or more resources from an organization's datasets."*/

function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  .groupBy(["distinct_id","properties.org id"],mixpanel.reducer.count())
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
/* VER 1.0
gets all page view events and counts unique combinations of week and org.  This is to say, if a single user looked at 3 different datasets from a single organization and then looked at the organization page as well (4 total page views) in a given week, the count returned by this query for that week would be 4.  It answers the question "How many page views did an organization's content receive in a given week."*/

function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "page view", selector: 'properties["org id"] != ""'}}]
  }})
  .groupBy(["properties.org id",mixpanel.numeric_bucket('time',mixpanel.weekly_time_buckets)],mixpanel.reducer.count())
  .sortAsc(function(row){{return row.key[1]}})
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
/* VER 1.0
selects all download events, counts unique combinations of week, user, resource, and org, then counts the number of those unique combinations by org.  That is to say if a single user downloaded 10 different resources two times each (20 total downloads) from a given org in a given week, the count returned by this query would be 10*/

function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  .groupBy(["distinct_id","properties.resource id","properties.org id",mixpanel.numeric_bucket('time',mixpanel.daily_time_buckets)],mixpanel.reducer.count())
  .groupBy(["key.2",(mixpanel.numeric_bucket('key.3',mixpanel.weekly_time_buckets))],mixpanel.reducer.count())
  .sortAsc(function(row){{return row.key[1]}})
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
/* VER 1.0
unique (by distinct id, resource id, dataset id, org id) downloads by dataset id (24 weeks, used for top downloads on org page)*/

/*selects all download events, counts unique combinations of day, user, resource, dataset, and org, then counts the number of those unique combinations by dataset.  That is to say if a single user downloaded 10 different resources two times each (20 total downloads) from a single dataset in a given day (and on no other days), the count returned by this query would be 10*/

function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  .groupBy(["distinct_id","properties.resource id",mixpanel.numeric_bucket('time',mixpanel.daily_time_buckets),"properties.dataset id", "properties.org id"],mixpanel.reducer.count())
  .groupBy([function(row) {{return row.key.slice(4)}}, function(row) {{return row.key.slice(3)}}],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      org_id: r.key[0],
      dataset_id: r.key[1],
      value: r.value
    }};
  }})
  .sortDesc('value');
}}
'''