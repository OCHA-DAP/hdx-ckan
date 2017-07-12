DOWNLOADS_PER_DATASET = '''
function main() {{
  return Events({{
    from_date: '{}',
    to_date: '{}',
    event_selectors: [{{event: "resource download"}}]
  }})
  .groupBy(["distinct_id","properties.resource id","properties.dataset id"],mixpanel.reducer.count())
  .groupBy([function(row) {{return row.key.slice(2)}}],mixpanel.reducer.count())
  .map(function(r){{
    return {{
      dataset_id: r.key[0],
      value: r.value
    }};
  }});
}}
'''

