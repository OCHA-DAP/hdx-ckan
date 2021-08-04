import six

import ckan.plugins.toolkit as toolkit

from ckan.lib.navl.validators import default, ignore_missing
from ckan.logic.validators import boolean_validator


get_converter = toolkit.get_converter


def showcase_update_schema_wrapper(original_schema):
    def schema_function():
        schema = original_schema()
        schema.update({
            'in_dataviz_gallery': [default('false'), boolean_validator, get_converter('convert_to_extras')],
            'in_carousel_section': [default('false'), boolean_validator, get_converter('convert_to_extras')],
            'dataviz_label': [ignore_missing, six.text_type, get_converter('convert_to_extras')],
        })
        return schema
    return schema_function


def showcase_show_schema_wrapper(original_schema):
    def schema_function():
        schema = original_schema()
        schema.update({
            'in_dataviz_gallery': [get_converter('convert_from_extras'), default('false'), boolean_validator],
            'in_carousel_section': [get_converter('convert_from_extras'), default('false'), boolean_validator],
            'dataviz_label': [get_converter('convert_from_extras'), ignore_missing],

        })
        return schema
    return schema_function
