import six

from ckanext.hdx_search.helpers.constants import DEFAULT_SORTING
from ckanext.hdx_users.helpers.constants import (
    ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT_WITH_ORG,
    ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT,
    ONBOARDING_START_PAGE_HDX_CONNECT,
    ONBOARDING_START_PAGE_CONTACT_CONTRIBUTOR,
    ONBOARDING_START_PAGE_ADD_DATA,
)
from ckanext.hdx_theme.helpers.ui_constants import CONSTANTS as UI_CONSTANTS
from ckanext.security.validators import MIN_PASSWORD_LENGTH, MIN_LEN_ERROR

CONSTANTS = {
    'DEFAULT_SORTING': DEFAULT_SORTING,
    'MOBILE_MEDIA': 'only screen and (max-width: 640px)',
    'PY3': six.PY3,
    'UI_CONSTANTS': UI_CONSTANTS,
    'ONBOARDING': {
        'VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT_WITH_ORG': ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT_WITH_ORG,
        'VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT': ONBOARDING_VALUE_PROPOSITION_INDIVIDUAL_ACCOUNT,
        'START_PAGE_HDX_CONNECT': ONBOARDING_START_PAGE_HDX_CONNECT,
        'START_PAGE_CONTACT_CONTRIBUTOR': ONBOARDING_START_PAGE_CONTACT_CONTRIBUTOR,
        'START_PAGE_ADD_DATA': ONBOARDING_START_PAGE_ADD_DATA,
    },
    'PASSWORD_RULES': MIN_LEN_ERROR.format(MIN_PASSWORD_LENGTH),
}


def const(constant_name):
    return CONSTANTS[constant_name]
