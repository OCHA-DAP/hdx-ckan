import dateutil.parser as dateutil_parser

import ckan.plugins.toolkit as tk

Invalid = tk.Invalid
_ = tk._


def daterange_parser(daterange_string, for_solr):
    '''

    :param daterange_string: string representing a daterange
    :type daterange_string: basestring
    :return:  returns a tuple of strings (star,end) if format is correct, otherwise raises Invalid
    :rtype: tuple(str,str)
    '''

    format_err_msg = _('daterange does not have the format: [start_datetime TO end_datetime]')
    empty_err_msg = _('daterange does not have the format: [start_datetime TO end_datetime]')
    start_date_err_msg = _('start datetime needs to be in isoformat, ex: 2019-01-21T12:25:05.955199')
    end_date_err_msg = _('end datetime needs to be "*" or in isoformat, ex: 2019-01-21T12:25:05.955199')

    if not daterange_string:
        raise Invalid(empty_err_msg)
    if not daterange_string.startswith('[') or not daterange_string.endswith(']'):
        raise Invalid(format_err_msg)

    stripped_value = daterange_string[1:-1]
    parts = stripped_value.split()
    if len(parts) != 3:
        raise Invalid(format_err_msg)

    try:
        start_date = dateutil_parser.parse(parts[0])
        start_date_str = start_date.isoformat()[:23] + ('Z' if for_solr else '')
    except Exception as e:
        raise Invalid(start_date_err_msg)

    if parts[1] != 'TO':
        raise Invalid(format_err_msg)

    if parts[2] != '*':
        try:
            end_date = dateutil_parser.parse(parts[2])
            end_date_str = end_date.isoformat()[:23] + ('Z' if for_solr else '')
        except Exception as e:
            raise Invalid(end_date_err_msg)
    else:
        end_date_str = '*'

    return '[{} TO {}]'.format(start_date_str, end_date_str)
