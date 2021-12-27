from ckanext.hdx_search.helpers.constants import DEFAULT_SORTING
import six

CONSTANTS = {
    'DEFAULT_SORTING': DEFAULT_SORTING,
    'MOBILE_MEDIA': 'only screen and (max-width: 640px)',
    'PY3': six.PY3,
}


def const(constant_name):
    return CONSTANTS[constant_name]
