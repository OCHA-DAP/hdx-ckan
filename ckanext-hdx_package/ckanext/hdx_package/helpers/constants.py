from collections import OrderedDict

FILE_WAS_UPLOADED = 'file-was-uploaded'


BATCH_MODE = 'batch_mode'

# DONT_GROUP - instructs a package_update to not use any batch code
BATCH_MODE_DONT_GROUP = 'DONT_GROUP'

# KEEP_OLD - instructs a package_update to keep the code from before this update
BATCH_MODE_KEEP_OLD = 'KEEP_OLD'

UNWANTED_DATASET_PROPERTIES = ['author_email', 'author']

COD_WITH_SERVICE = 'cod-with-service'
COD_WITHOUT_SERVICE = 'cod-without-service'
COD_CANDIDATE = 'candidate-cod'
COD_NOT = 'not-cod'

COD_VALUES_MAP = OrderedDict((
    (COD_NOT, 'Not COD'),
    (COD_CANDIDATE, 'COD candidate'),
    (COD_WITHOUT_SERVICE, 'COD without service'),
    (COD_WITH_SERVICE, 'COD with service'),
))
