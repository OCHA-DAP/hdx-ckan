import datetime


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


def generate_datetime_period_query(field_name, last_x_days, include_leading_space=False, exclude=False, include=False):
    '''
    :param field_name:
    :type field_name: str
    :param last_x_days:
    :type last_x_days: int
    :param exclude: whether to add a "-" to the query
    :type exclude: bool
    :param include: whether to add a "+" to the query
    :type include: bool
    :return:
    :rtype: str
    '''
    params = {
        'field_name': field_name,
        'leading_space': ' ' if include_leading_space else '',
        'now_string': datetime.datetime.utcnow().isoformat() + 'Z',
        'x_days': last_x_days,
        'boolean_operator': '-' if exclude else '+' if include else ''
    }
    query = '{leading_space}{boolean_operator}{field_name}:[{now_string}-{x_days}DAYS TO {now_string}]'.format(**params)
    return query
