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
                        'considered to be the best-available dataset for the given location. '
                        'Available as downloadable files.',
     }
     ),
    (COD_STANDARD,
     {
         'title': 'Standard COD',
         'is_cod': True,
         'explanation': 'A COD that has been accepted for use by the humanitarian community, but has not yet gone '
                        'through the standardization process to become an enhanced COD. '
                        'Available as downloadable files.',
     }
     ),
    (COD_ENHANCED,
     {
         'title': 'Enhanced COD',
         'is_cod': True,
         'explanation': 'A COD that has been standardized. Available in a range of formats and '
                        'machine-readable services.'
     }
     ),
))

for i, cod_value in enumerate(COD_VALUES_MAP.values()):
    cod_value['index'] = i

COD_GROUP_EXPLANATION_LINK = 'https://storymaps.arcgis.com/stories/dcf6135fc0e943a9b77823bb069e2578'

UPDATE_FREQ_LIVE = '0'

S3_TAG_KEY_DATASET_NAME = 'DatasetName'
S3_TAG_KEY_SENSITIVE = 'Sensitive'
S3_TAG_VALUE_SENSITIVE_TRUE = 'yes'
S3_TAG_VALUE_SENSITIVE_FALSE = 'no'

PACKAGE_METADATA_FIELDS_MAP = {'id': 'Dataset ID', 'title': 'Title of Dataset', 'name': 'Dataset URL',
                               'notes': 'Description', 'dataset_source': 'Source', 'organization': 'Contributor',
                               'dataset_date': 'Reference Period', 'last_modified': 'Updated',
                               'data_update_frequency': 'Expected Update Frequency', 'groups': 'Location',
                               'license_title': 'License', 'methodology': 'Methodology',
                               'methodology_other': 'Define Methodology', 'caveats': 'Caveats/Comments', 'tags': 'Tags'}

RESOURCE_METADATA_FIELDS_MAP = {'created': 'Created', 'description': 'Description', 'format': 'File Format',
                                'download_url': 'Download URL', 'id': 'Resource ID', 'last_modified': 'Updated',
                                'metadata_modified': 'Metadata Updated', 'microdata': 'Microdata',
                                'package_id': None, 'dataset_id': 'Dataset ID', 'resource_type': 'Resource Type',
                                'name': 'Resource Name',
                                'mimetype': 'MIME Type', 'size': 'Size'}
