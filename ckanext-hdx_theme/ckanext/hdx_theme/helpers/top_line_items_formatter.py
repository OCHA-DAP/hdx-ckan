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


class FormatterGettersSetters(object):
    @staticmethod
    def top_line_date_get(r):
        return r[u'latest_date']

    @staticmethod
    def top_line_date_set(r, value):
        r[u'latest_date'] = value

    @staticmethod
    def spark_line_date_get(r):
        return r['date']

    @staticmethod
    def spark_line_date_set(r, value):
        r['date'] = value

    @staticmethod
    def top_line_value_get(r):
        return r[u'value']

    @staticmethod
    def top_line_value_set(r, value):
        r[u'formatted_value'] = value

    @staticmethod
    def spark_line_value_get(r):
        return r['value']

    @staticmethod
    def spark_line_value_set(r, value):
        r['value'] = value

    @staticmethod
    def top_line_unit_get(r):
        return r[u'units']


class TopLineItemsFormatter:
    '''
    Formats the values in the given topline numbers. If they have sparklines then it tries to
    format the values of the sparklines as well.

    It doesn't format the date. The _format_date() function is just a dummy that should be overridden
    like in TopLineItemsWithDateFormatter class.

    Getting and setting the values is abstracted by the use of the static functions in FormatterGettersSetters.
    '''

    def __init__(self, top_line_items, getter_setter_class=FormatterGettersSetters):
        '''
        :param top_line_items:
        :type top_line_items: list
        '''
        self.top_line_items = top_line_items
        self.getter_setter_class = getter_setter_class

    def format_results(self):

        gs = self.getter_setter_class
        self._format_results(self.top_line_items, gs.top_line_date_get, gs.top_line_date_set,
                             gs.top_line_value_get, gs.top_line_value_set, gs.top_line_unit_get)

    def _format_results(self, records, date_getter, date_setter, value_getter,
                        value_setter, unit_getter, level=0):
        '''

        :param records: toplines
        :type records: list
        :param level: the depth in the records hierarchy. Values are formatted only for level ZERO OR for 'ratio' units
        :type level: int
        '''

        gs = self.getter_setter_class

        for r in records:
            if 'sparklines' in r:
                self._format_results(r['sparklines'], gs.spark_line_date_get, gs.spark_line_date_set,
                    gs.spark_line_value_get, gs.spark_line_value_set,
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
    '''
    See TopLineItemsFormatter documentation
    '''

    def __init__(self, top_line_items, getter_setter_class=FormatterGettersSetters,
                 src_date_format='%Y-%m-%dT%H:%M:%S', dest_date_format='%b %d, %Y'):
        TopLineItemsFormatter.__init__(self, top_line_items, getter_setter_class)

        self.src_date_format = src_date_format
        self.dest_date_format = dest_date_format

    def _format_date(self, r, date_getter, date_setter):
        try:
            d = dt.datetime.strptime(date_getter(r), self.src_date_format)
            date_setter(r, dt.datetime.strftime(d, self.dest_date_format))
        except Exception, e:
            log.error('Problem reading date: ' + str(e))
