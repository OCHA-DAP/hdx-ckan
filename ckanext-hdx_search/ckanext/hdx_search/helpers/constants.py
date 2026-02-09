from ckanext.hdx_package.helpers.constants import HPC_VALUES_MAP

DEFAULT_SORTING = 'last_modified desc'
DEFAULT_NUMBER_OF_ITEMS_PER_PAGE = 10

NEW_DATASETS_FACET_NAME = 'new_datasets'
UPDATED_DATASETS_FACET_NAME = 'updated_datasets'
BULK_DATASETS_FACET_NAME = 'bulk_datasets'
PRIVATE_DATASETS_FACET_NAME = 'private_datasets'

HXLATED_DATASETS_FACET_NAME = 'hxl'
HXLATED_DATASETS_FACET_QUERY = 'vocab_Topics:hxl'

# SADD_DATASETS_FACET_NAME = 'sadd'  # sex and age disaggregated data
# SADD_DATASETS_FACET_QUERY = \
#     'vocab_Topics:("sex and age disaggregated data - sadd" OR "sex and age disaggregated data-sadd")'

# ADMIN_DIVISIONS_DATASETS_FACET_NAME = 'administrative_divisions'
# ADMIN_DIVISIONS_DATASETS_FACET_QUERY = \
#     'vocab_Topics:("administrative divisions" OR "administrative boundaries-divisions")'

COD_DATASETS_FACET_NAME = 'cod'
COD_DATASETS_FACET_QUERY = 'vocab_Topics:("common operational dataset - cod" OR "common operational dataset-cod")'

HPC_QUOTED_TAGS = (f'"{item}"' for item in HPC_VALUES_MAP.keys())
HPC_DATASETS_FACET_NAME = 'hpc'
HPC_DATASETS_FACET_QUERY = f'vocab_Topics:({" OR ".join(HPC_QUOTED_TAGS)})'

TABULAR_DATA_DATASETS_FACET_NAME = 'tabular_data'
TABULAR_DATA_DATASETS_FACET_QUERY = 'res_extras_datastore_active:true'

P_CODED_DATASET_FACET_NAME = 'p_coded'
SUBNATIONAL_DATASETS_FACET_NAME = 'subnational'
GEODATA_DATASETS_FACET_NAME = 'geodata'
REQUESTDATA_DATASETS_FACET_NAME = 'requestdata'
SHOWCASE_DATASETS_FACET_NAME = 'showcases'
ARCHIVED_DATASETS_FACET_NAME = 'archived'

HDX_HAPI_DATA_FACET_NAME = 'hdx_hapi'
HDX_HAPI_DATA_FACET_QUERY = 'organization:hdx-hapi'

STATUS_PRIORITIES = {
    '': 0,
    'OK': 1,
    'RUNNING': 2,
    'QUEUED': 3,
    'FINDINGS': 4,
    'ERROR': 5,
    'EXCEPTION': 5,
    False: 1,
    True: 2
}


