

import ckanext.hdx_theme.helpers.top_line_items_formatter as formatter

class TestFormatter(object):

    def test_format_decimal_number(self):
        assert formatter.format_decimal_number(84.00) == '84'
        assert formatter.format_decimal_number(83.100) == '83.1'
        assert formatter.format_decimal_number(83.987) == '84'