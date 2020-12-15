import dateutil.parser as dateutil_parser

import ckan.plugins.toolkit as tk

Invalid = tk.Invalid
_ = tk._
h = tk.h # helpers


class DaterangeParser(object):

    def __init__(self, daterange_string):
        '''
        :param daterange_string: string representing a daterange
        :type daterange_string: basestring
        '''

        self.format_err_msg = _('date range does not have the format: [start_datetime TO end_datetime]')
        self.empty_err_msg = _('date range does not have the format: [start_datetime TO end_datetime]')
        self.start_date_err_msg = _('start datetime needs to be in isoformat, ex: 2019-01-21T12:25:05.955199')
        self.end_date_err_msg = _('end datetime needs to be "*" or in isoformat, ex: 2019-01-21T12:25:05.955199')
        self.end_date_before_start_date_err_msg = _('end datetime needs to be after start datetime')

        super(DaterangeParser, self).__init__()

        if not daterange_string:
            raise Invalid(self.empty_err_msg)
        if not daterange_string.startswith('[') or not daterange_string.endswith(']'):
            raise Invalid(self.format_err_msg)

        stripped_value = daterange_string[1:-1]
        parts = stripped_value.split()
        if len(parts) != 3:
            raise Invalid(self.format_err_msg)

        try:
            self.start_date = dateutil_parser.parse(parts[0])
        except Exception as e:
            raise Invalid(self.start_date_err_msg)

        if parts[1] != 'TO':
            raise Invalid(self.format_err_msg)

        if parts[2] != '*':
            self.end_date_is_infinity = False
            try:
                self.end_date = dateutil_parser.parse(parts[2])
            except Exception as e:
                raise Invalid(self.end_date_err_msg)
            if self.end_date < self.start_date:
                raise Invalid(self.end_date_before_start_date_err_msg)
        else:
            self.end_date_is_infinity = True

    # def is_valid(self):
    #     if self.start_date and (self.end_date_is_infinity or self.end_date):
    #         return True
    #     return False

    def compute_daterange_string(self, for_solr, end_date_ending=False):
        start_date_str = self.start_date.isoformat()[:23] + ('Z' if for_solr else '')
        if self.end_date_is_infinity:
            end_date_str = '*'
        else:
            end_date_str = self.end_date.isoformat()[:23] + ('Z' if for_solr else '')
            if end_date_ending and '00:00:00' in end_date_str:
                end_date_str = end_date_str.replace('00:00:00', '23:59:59')

        return '[{} TO {}]'.format(start_date_str, end_date_str)

    # def human_readable(self):
    #     start_date_str = h.render_datetime(self.start_date)
    #     if self.end_date_is_infinity:
    #         end_date_str = _('OPEN ENDED')
    #     else:
    #         end_date_str = h.render_datetime(self.end_date)
    #
    #     return '{} - {}'.format(start_date_str, end_date_str)

