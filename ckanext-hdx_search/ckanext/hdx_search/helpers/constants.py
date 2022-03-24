DEFAULT_SORTING = 'if(gt(last_modified,review_date),last_modified,review_date) desc'
DEFAULT_NUMBER_OF_ITEMS_PER_PAGE = 25

NEW_DATASETS_FACET_NAME = 'new_datasets'
UPDATED_DATASETS_FACET_NAME = 'updated_datasets'
DELINQUENT_DATASETS_FACET_NAME = 'delinquent_datasets'
BULK_DATASETS_FACET_NAME = 'bulk_datasets'

HXLATED_DATASETS_FACET_NAME = 'hxl'
HXLATED_DATASETS_FACET_QUERY = 'vocab_Topics:hxl'

SADD_DATASETS_FACET_NAME = 'sadd'  # sex and age disaggregated data
SADD_DATASETS_FACET_QUERY = 'vocab_Topics:"sex and age disaggregated data - sadd"'

ADMIN_DIVISIONS_DATASETS_FACET_NAME = 'administrative_divisions'
ADMIN_DIVISIONS_DATASETS_FACET_QUERY = 'vocab_Topics:"administrative divisions"'

COD_DATASETS_FACET_NAME = 'cod'
COD_DATASETS_FACET_QUERY = 'vocab_Topics:"common operational dataset - cod"'

SUBNATIONAL_DATASETS_FACET_NAME = 'subnational'
QUICKCHARTS_DATASETS_FACET_NAME = 'quickcharts'
GEODATA_DATASETS_FACET_NAME = 'geodata'
REQUESTDATA_DATASETS_FACET_NAME = 'requestdata'
SHOWCASE_DATASETS_FACET_NAME = 'showcases'
ARCHIVED_DATASETS_FACET_NAME = 'archived'

STATUS_PRIORITIES = {
    '': 0,
    'OK': 1,
    'RUNNING': 2,
    'QUEUED': 3,
    'ERROR': 4
}

