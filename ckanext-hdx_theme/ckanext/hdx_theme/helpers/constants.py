from ckanext.hdx_search.helpers.constants import DEFAULT_SORTING

CONSTANTS = {
    'DEFAULT_SORTING': DEFAULT_SORTING
}


def const(constant_name):
    return CONSTANTS[constant_name]
