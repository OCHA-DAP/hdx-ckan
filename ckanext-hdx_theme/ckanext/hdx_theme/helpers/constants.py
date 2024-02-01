import six

from ckanext.hdx_search.helpers.constants import DEFAULT_SORTING
from ckanext.hdx_theme.helpers.ui_constants import CONSTANTS as UI_CONSTANTS

CONSTANTS = {
    'DEFAULT_SORTING': DEFAULT_SORTING,
    'MOBILE_MEDIA': 'only screen and (max-width: 640px)',
    'PY3': six.PY3,
    'UI_CONSTANTS': UI_CONSTANTS,
}


def const(constant_name):
    return CONSTANTS[constant_name]
