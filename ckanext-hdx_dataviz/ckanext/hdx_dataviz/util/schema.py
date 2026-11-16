import ckan.plugins.toolkit as toolkit
import ckanext.hdx_dataviz.helpers.helpers as h
from ckan.lib.navl.validators import default, ignore_missing, ignore_empty
from ckan.logic.validators import boolean_validator, url_validator, natural_number_validator

get_converter = toolkit.get_converter
Invalid = toolkit.Invalid
StopOnError = toolkit.StopOnError
unicode_safe = toolkit.get_validator('unicode_safe')
_ = toolkit._


def showcase_update_schema_wrapper(original_schema):
    def schema_function():
        schema = original_schema()
        schema.update({
            'in_dataviz_gallery': [_has_dataviz_gallery_permission, default('false'), boolean_validator,
                                   get_converter('convert_to_extras')],
            'image_frame_mode': [_has_dataviz_gallery_permission, default('false'), boolean_validator,
                                   get_converter('convert_to_extras')],
            'in_carousel_section': [_has_dataviz_gallery_permission, default('false'), boolean_validator,
                                    get_converter('convert_to_extras')],
            'dataviz_label': [_has_dataviz_gallery_permission, ignore_missing, unicode_safe,
                              get_converter('convert_to_extras')],
            'data_url': [_has_dataviz_gallery_permission, ignore_empty, _is_https_url, url_validator,
                         get_converter('convert_to_extras')],
            'priority': [_has_dataviz_gallery_permission, ignore_empty, natural_number_validator,
                         get_converter('convert_to_extras')],
        })
        return schema
    return schema_function


def showcase_show_schema_wrapper(original_schema):
    def schema_function():
        schema = original_schema()
        schema.update({
            'in_dataviz_gallery': [get_converter('convert_from_extras'), default('false'), boolean_validator],
            'image_frame_mode': [get_converter('convert_from_extras'), default('false'), boolean_validator],
            'in_carousel_section': [get_converter('convert_from_extras'), default('false'), boolean_validator],
            'dataviz_label': [get_converter('convert_from_extras'), ignore_missing],
            'data_url': [get_converter('convert_from_extras'), ignore_empty],
            'priority': [get_converter('convert_from_extras'), ignore_empty, natural_number_validator],

        })
        return schema
    return schema_function


def _is_https_url(value, context):
    if 'https://' not in value:
        raise Invalid(_('Only HTTPS URLs are allowed'))
    return value


def _has_dataviz_gallery_permission(key, data, errors, context):
    '''Inspired by ignore_not_sysadmin() validator from core'''

    user = context.get('user')
    has_permission = h.has_dataviz_gallery_permission(user)
    if has_permission:
        return
    data.pop(key)
    raise StopOnError
