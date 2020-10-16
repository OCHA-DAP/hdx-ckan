from collections import OrderedDict

FILE_WAS_UPLOADED = 'file-was-uploaded'


BATCH_MODE = 'batch_mode'

# DONT_GROUP - instructs a package_update to not use any batch code
BATCH_MODE_DONT_GROUP = 'DONT_GROUP'

# KEEP_OLD - instructs a package_update to keep the code from before this update
BATCH_MODE_KEEP_OLD = 'KEEP_OLD'

UNWANTED_DATASET_PROPERTIES = ['author_email', 'author']

COD_ENHANCED = 'cod-enhanced'
COD_STANDARD = 'cod-standard'
COD_CANDIDATE = 'cod-candidate'
COD_NOT = 'not-cod'

COD_VALUES_MAP = OrderedDict((
    (COD_NOT,
     {
         'title': 'Not COD',
         'is_cod': False,
     }
     ),
    (COD_CANDIDATE,
     {
         'title': 'Candidate COD',
         'is_cod': True,
         'explanation': 'A dataset that is considered a starting point for the COD process and is generally '
                        'considered to be the best-available dataset for the given location.',
     }
     ),
    (COD_STANDARD,
     {
         'title': 'Standard COD',
         'is_cod': True,
         'explanation': 'A COD that has been endorsed by the humanitarian community, but has not yet gone through the '
                        'standardization process to become an enhanced COD.',
     }
     ),
    (COD_ENHANCED,
     {
         'title': 'Enhanced COD',
         'is_cod': True,
         'explanation': 'A COD that has been endorsed and has been standardized. Available in a range of formats and '
                        'machine-readable services.'
     }
     ),
))

for i, cod_value in enumerate(COD_VALUES_MAP.values()):
    cod_value['index'] = i

COD_GROUP_EXPLANATION_LINK = 'https://en.wikipedia.org/wiki/Common_Operational_Datasets'

UPDATE_FREQ_LIVE = '0'
