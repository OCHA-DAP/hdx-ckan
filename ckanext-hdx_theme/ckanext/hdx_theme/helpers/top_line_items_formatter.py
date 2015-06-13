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


def round_up_x_decimal_value(value, x):
    zeroes_str = (x-1)*'0'
    decimal_format = '.' + zeroes_str + '1'
    decimal_value = Decimal(str(value)).quantize(
        Decimal(decimal_format), rounding=decimal.ROUND_HALF_UP)
    return decimal_value


def round_up_decimal_value(value):
    decimal_value = Decimal(str(value)).quantize(
        Decimal('1.'), rounding=decimal.ROUND_HALF_UP)
    return decimal_value

def format_decimal_number(value, places=1):
    places_format = '{}f'.format(places)
    format = '{:,.' + places_format + '}'
    rounded_value = round_up_x_decimal_value(value, places)
    int_value = int(rounded_value)
    if int_value == rounded_value:
        formatted_value = '{:,}'.format(int_value)
    else:
        formatted_value = format.format(rounded_value)
    return formatted_value


class TopLineItemsFormatter:

    def __init__(self, top_line_items):
        self.top_line_items = top_line_items

    def format_results(self):

        self._format_results(self.top_line_items, top_line_date_get,
                             top_line_date_set, top_line_value_get,
                             top_line_value_set, top_line_unit_get)

    def _format_results(self, records, date_getter, date_setter, value_getter,
                        value_setter, unit_getter, level=0):
        for r in records:
            if 'sparklines' in r:
                self._format_results(
                    r['sparklines'], spark_line_date_get, spark_line_date_set,
                    spark_line_value_get, spark_line_value_set,
                    lambda t: unit_getter(r), level=1)
                r['sparklines_json'] = json.dumps(r['sparklines'])

            self._format_date(r, date_getter, date_setter)

            if level == 0 or unit_getter(r) == 'ratio':
                modified_value = value_getter(r)
                if unit_getter(r) == 'ratio':
                    modified_value = self._format_ratio(modified_value)
                elif unit_getter(r) == 'per100k':
                    modified_value = self._format_per100k(modified_value)
                elif unit_getter(r) in ('million', 'dollars_million'):
                    modified_value = self._format_million(modified_value)
                elif unit_getter(r) == 'count':
                    modified_value = self._format_decimal_number(
                        modified_value)
                elif unit_getter(r) == 'dollars':
                    modified_value = round_up_decimal_value(
                        modified_value)
                    modified_value = self._format_decimal_number(
                        modified_value)

                value_setter(r, modified_value)

    def _format_ratio(self, original_value):
        modified_value = original_value * 100.0

        formatted_value = self._format_decimal_number(modified_value)
        return formatted_value

    def _format_per100k(self, original_value):
        modified_value = original_value * 100000.0

        formatted_value = self._format_decimal_number(modified_value)
        return formatted_value

    def _format_million(self, original_value):
        modified_value = original_value / 1000000.0

        formatted_value = self._format_decimal_number(modified_value)
        return formatted_value

    def _format_decimal_number(self, value):
        return format_decimal_number(value)

    def _format_date(self, r, date_getter, date_setter):
        pass


class TopLineItemsWithDateFormatter (TopLineItemsFormatter):

    def _format_date(self, r, date_getter, date_setter):
        try:
            d = dt.datetime.strptime(date_getter(r), '%Y-%m-%dT%H:%M:%S')
            date_setter(r, dt.datetime.strftime(d, '%b %d, %Y'))
        except Exception, e:
            log.error('Problem reading date: ' + str(e))
