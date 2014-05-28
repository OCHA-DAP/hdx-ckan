'''
Created on May 16, 2014

@author: alexandru-m-g

'''

import ckan.tests as tests
import webtest
import ckan.lib.helpers as h
import ckan.plugins as p
import ckan.lib.plugins as pl
import ckan.lib.create_test_data as ctd
import ckan.lib.search as search
import ckan.model as model
import ckan.plugins.toolkit as tk
import ckanext.metadata_fields.plugin as thisplugin
import unicodedata

from ckan.config.middleware import make_app
from pylons import config

class TestDatasetOutput(tests.WsgiAppCase):
    
    @classmethod
    def setup_class(cls):
#         p.load('metadata_fields')
#         TestMetadataFields.get_app()
        search.clear()
        model.Session.remove()
        ctd.CreateTestData.create()
        
      
    @classmethod
    def teardown_class(cls):
        model.Session.remove()
        model.repo.rebuild_db()
        p.unload('hdx_theme')
        
    def test_deleted_badge_appears(self):
        p.load('hdx_theme')
        testsysadmin = model.User.by_name('testsysadmin')
        dataset_name = 'test-dataset'
        result = tests.call_action_api(self.app, 'package_create', name=dataset_name,
                private=False, package_creator='test-creator', source='sample source',
                apikey=testsysadmin.apikey, status=200)
        page = self._getPackagePage(dataset_name)
        assert not 'Deleted' in str(page.response), 'Page should not have deleted badge as it was not deleted'
        
        deleted_result = tests.call_action_api(self.app, 'package_delete',
                apikey=testsysadmin.apikey, id=dataset_name)
        
        deleted_page = self._getPackagePage(dataset_name, testsysadmin.apikey)
        #print deleted_page.response
        assert 'Deleted' in str(deleted_page.response), 'Page needs to have deleted badge'
        
    def _getPackagePage(self, package_id, apikey=None):
        page = None
        url = h.url_for(controller='package', action='read', id=package_id)
        if apikey:
            page = self.app.get(url,headers={'Authorization':unicodedata.normalize('NFKD', apikey).encode('ascii','ignore')})
        else:
            page = self.app.get(url)
        return page
        

