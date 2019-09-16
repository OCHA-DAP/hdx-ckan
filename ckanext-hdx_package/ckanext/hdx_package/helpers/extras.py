import ckan.plugins.toolkit as tk


ALLOWED_EXTRAS = {
    'review_date': None,
    'data_update_frequency': None,
    'is_requestdata_type': [tk.get_validator('boolean_validator')],
}


def get_extra_from_dataset(field_name, dataset_dict):
    result = None
    if field_name in dataset_dict:
        result = dataset_dict[field_name]

    # When a dataset is indexed in solr the package dict returned by package_show
    # leaves the extras fields unprocessed in an extras list so that they get indexed as extras_* fields in solr
    elif 'extras' in dataset_dict and field_name in ALLOWED_EXTRAS:
        result = next(
            (extra.get('value') for extra in dataset_dict.get('extras')
             if extra.get('state') == 'active' and extra.get('key') == field_name),
            {})
        if result and ALLOWED_EXTRAS[field_name]:
            for func in ALLOWED_EXTRAS[field_name]:
                result = func(result, {})

    return result
