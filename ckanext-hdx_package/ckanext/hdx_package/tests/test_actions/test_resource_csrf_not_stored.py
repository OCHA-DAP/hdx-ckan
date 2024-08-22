import pytest

import ckan.plugins.toolkit as tk
import ckan.model as model

from typing import Dict, cast
from ckan.types import Context

_get_action = tk.get_action


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'clean_db', 'clean_index')
def test_csrf_not_stored_in_resource(dataset_with_uploaded_resource: Dict):
    resource_dict: Dict = dataset_with_uploaded_resource['resources'][0]
    for key in resource_dict.keys():
        assert 'csrf_token' not in key

    context = cast(Context, {'model': model, 'session': model.Session, 'user': 'test_hdx_sysadmin_user'})
    modified_resource_dict = _get_action('resource_patch')(context, {
        'id': resource_dict['id'],
        '_csrf_token': 'abcdef'
    })
    for key in modified_resource_dict.keys():
        assert 'csrf_token' not in key, 'csrf_token should not be saved in resource'
