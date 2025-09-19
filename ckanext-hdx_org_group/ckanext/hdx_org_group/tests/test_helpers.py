"""
reCreated on 19 Sep, 2023

@author: dan
"""

import pytest
import json
import logging as logging
import ckanext.hdx_org_group.helpers.organization_helper as helper
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.types import Context
import ckanext.hdx_package.helpers.caching as caching
from ckanext.hdx_org_group.tests.conftest import ORG

_get_action = tk.get_action
NotAuthorized = tk.NotAuthorized
NotFound = tk.ObjectNotFound
log = logging.getLogger(__name__)


@pytest.mark.usefixtures('keep_db_tables_on_clean', 'hdx_clean_db', 'clean_index', 'setup_user_data')
class TestHelpers(object):

    def test_filter_and_sort_results_case_insensitive(self,app):
        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}

        caching.invalidate_cached_organization_list()
        cached_all_orgs = _get_action('cached_organization_list')(sysadmin_context, {})
        q='hdx-test-org'
        sort_option_list = ['title asc', 'title desc', 'datasets asc', 'datasets desc', 'popularity']
        for sort_option in sort_option_list:
            all_orgs = helper.filter_and_sort_results_case_insensitive(cached_all_orgs, sort_option, q=q, has_datasets=True)
            assert len(all_orgs)>0

    def test_get_viz_title_from_extras(self, app):
        sysadmin_context: Context = {'model': model, 'session': model.Session, 'user': 'testsysadmin'}
        json_config_wfp = '''
                    {
                        "visualization-select": "WFP",
                        "viz-title": "Test Visualization Title",
                        "viz-data-link-url": "https://data.humdata.org/dataset/wfp-food-prices",
                        "viz-resource-id": "test-resource-id"
                    }
                '''
        caching.invalidate_cached_organization_list()
        org_dict = _get_action('organization_show')(sysadmin_context, {'id': ORG})
        org_dict.update({
            'visualization_config': json_config_wfp,
            'custom_org': '1',
            'customization': json.dumps({
                'topline_resource': 'test-topline-resource',
            }),
        })
        org_dict = _get_action('organization_update')(sysadmin_context, org_dict)
        result = helper.get_viz_title_from_extras(org_dict)
        assert 'Test Visualization Title' == result
