'''
Created on Nov 6, 2014

@author: alexandru-m-g
'''
import logging as logging

import ckan.plugins.toolkit as tk
import ckan.model as model
import ckan.lib.helpers as h
import ckan.common as common

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base
import ckanext.hdx_search.controllers.search_controller as search_controller

c = common.c

log = logging.getLogger(__name__)

indicator_counts = 0
dataset_counts = 0

performing_search_original = search_controller.HDXSearchController._performing_search


def performing_search_wrapper(self, *args):
    global indicator_counts
    global dataset_counts
    ret = performing_search_original(self, *args)
    indicator_counts = c.indicator_counts
    dataset_counts = c.dataset_counts
    return ret


search_controller.HDXSearchController._performing_search = performing_search_wrapper


packages = [
    {
        "package_creator": "test function",
        "private": False,
        "dataset_date": "01/01/1960-12/31/2012",
        "indicator": "1",
        "caveats": "These are the caveats",
        "license_other": "TEST OTHER LICENSE",
        "methodology": "This is a test methodology",
        "dataset_source": "World Bank",
        "license_id": "hdx-other",
        "name": "test_indicator_1",
        "notes": "This is a hdxtest indicator",
        "title": "Test Indicator 1",
        "indicator": 1,
        "groups": [{"name": "roger"}]
    },
    {
        "package_creator": "test function",
        "private": False,
        "dataset_date": "01/01/1960-12/31/2012",
        "caveats": "These are the caveats",
        "license_other": "TEST OTHER LICENSE",
        "methodology": "This is a test methodology",
        "dataset_source": "World Bank",
        "license_id": "hdx-other",
        "name": "test_dataset_1",
        "notes": "This is a hdxtest dataset 1",
        "title": "Test Dataset 1",
        "groups": [{"name": "roger"}]
    },
    {
        "package_creator": "test function",
        "private": False,
        "dataset_date": "01/01/1960-12/31/2012",
        "caveats": "These are the caveats",
        "license_other": "TEST OTHER LICENSE",
        "methodology": "This is a test methodology",
        "dataset_source": "World Bank",
        "license_id": "hdx-other",
        "name": "test_dataset_2",
        "notes": "This is a hdxtest dataset 2",
        "title": "Test Dataset 2",
        "groups": [{"name": "roger"}]
    }
]

log = logging.getLogger(__name__)


class TestHDXSearchResults(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_search hdx_package hdx_theme')

    @classmethod
    def _get_action(cls, action_name):
        return tk.get_action(action_name)

    def test_hdx_search_results(self):
        global packages

#         testsysadmin = model.User.by_name('testsysadmin')

        for package in packages:
            context = {'ignore_auth': True,
                       'model': model, 'session': model.Session, 'user': 'nouser'}
            self._get_action('package_create')(context, package)
            # This is a copy of the hack done in dataset_controller
            self._get_action('package_update')(context, package)

        # Testing search on all tab
        url = h.url_for(
            'search', q='hdxtest')
        self.app.get(url)

        assert indicator_counts == 1, '1 indicator'
        assert dataset_counts == 2, '2 datasets'

        # Testing search on indicators tab
        url = h.url_for(
            'search', q='hdxtest', ext_indicator='1')
        self.app.get(url)

        assert indicator_counts == 1, '1 indicator'
        assert dataset_counts == 2, '2 datasets'

        search_controller.HDXSearchController._performing_search = performing_search_original
