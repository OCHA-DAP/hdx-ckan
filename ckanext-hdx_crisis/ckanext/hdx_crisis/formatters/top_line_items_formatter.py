'''
Created on Dec 2, 2014

@author: alexandru-m-g
'''

import logging
import datetime as dt
import decimal
import json

log = logging.getLogger(__name__)

Decimal = decimal.Decimal


def top_line_date_get(r):
    return r[u'latest_date']


def top_line_date_set(r, value):
    r[u'latest_date'] = value


def spark_line_date_get(r):
    return r['date']


def spark_line_date_set(r, value):
    r['date'] = value


def top_line_value_get(r):
    return r[u'value']


def top_line_value_set(r, value):
    r[u'formatted_value'] = value


def spark_line_value_get(r):
    return r['value']


def spark_line_value_set(r, value):
    r['value'] = value


def top_line_unit_get(r):
    return r[u'units']


class TopLineItemsFormatter:

    def __init__(self, top_line_items):
        self.top_line_items = top_line_items

    def _get_decimal_value(self, value):
        decimal_value = Decimal(str(value)).quantize(
            Decimal('.1'), rounding=decimal.ROUND_HALF_UP)
        return decimal_value

    def format_results(self):

        self._format_results(self.top_line_items, top_line_date_get,
                             top_line_date_set, top_line_value_get,
                             top_line_value_set, top_line_unit_get)

    def _format_results(self, records, date_getter, date_setter, value_getter, value_setter, unit_getter, level=0):
        for r in records:
            if 'sparklines' in r:
                self._format_results(
                    r['sparklines'], spark_line_date_get, spark_line_date_set,
                    spark_line_value_get, spark_line_value_set,
                    lambda t: unit_getter(r), level=1)
                r['sparklines_json'] = json.dumps(r['sparklines'])

            try:
                d = dt.datetime.strptime(date_getter(r), '%Y-%m-%dT%H:%M:%S')
                date_setter(r, dt.datetime.strftime(d, '%b %d, %Y'))
            except TypeError, e:
                log.error('Problem reading date: ' + str(e))

            if level == 0 or unit_getter(r) == 'ratio':
                modified_value = value_getter(r)
                if unit_getter(r) == 'ratio':
                    modified_value *= 100.0
                elif unit_getter(r) == 'million':
                    modified_value /= 1000000.0

                int_value = int(modified_value)
                if int_value == modified_value:
                    formatted_value = '{:,}'.format(int_value)
                else:
                    formatted_value = '{:,.1f}'.format(
                        self._get_decimal_value(modified_value))

                value_setter(r, formatted_value)
