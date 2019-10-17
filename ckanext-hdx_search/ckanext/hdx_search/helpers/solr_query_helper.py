def generate_facet_query_from_list(title, query_tag, doc_property, item_list, boolean_operator='OR', negate=False):
    filter_query = generate_filter_query_from_list(doc_property, item_list, boolean_operator, negate)

    quoted_title = '"{}"'.format(title)
    extra_params = 'tag={} key={}'.format(query_tag, quoted_title)
    query = '{!' + extra_params + '}' + filter_query
    return query


def generate_filter_query_from_list(doc_property, item_list, boolean_operator='OR', negate=False):
    spaced_operator = ' {} '.format(boolean_operator)
    quoted_items = ('"{}"'.format(t) for t in item_list)
    joined_tags = spaced_operator.join(quoted_items)
    prefix = '-' if negate else ''
    query = '{}{}: ({})'.format(prefix, doc_property, joined_tags)
    return query
