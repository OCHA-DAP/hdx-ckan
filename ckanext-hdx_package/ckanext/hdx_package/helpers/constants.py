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
    (COD_NOT, 'Not COD'),
    (COD_CANDIDATE, 'Candidate COD'),
    (COD_STANDARD, 'Standard COD'),
    (COD_ENHANCED, 'Enhanced COD'),
))


UPDATE_FREQ_LIVE = '0'
