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

from ckan.config.middleware import make_app
from pylons import config

class TestMetadataFields(tests.WsgiAppCase):
    
    @classmethod
    def setup_class(cls):
        p.load('metadata_fields')
#         TestMetadataFields.get_app()
        search.clear()
        model.Session.remove()
        ctd.CreateTestData.create()
        
        '''
        There is an ugly hack here. Apparently ckan's nosetest doesn't manage to set the correct 
        plugin (HdxMetadataFieldsPlugin) as the default package plugin. So we are forcing it here 
        and resetting it in teardown_class
        '''
        cls.original_default_package_plugin = pl._default_package_plugin
        pl._default_package_plugin = thisplugin.HdxMetadataFieldsPlugin()
      
    @classmethod
    def get_app(cls):
        '''
        Alternative method for creating a test app. Not needed if inheriting from WsgiAppCase
        '''
        if not 'ckan.plugins' in config:
            config['ckan.plugins'] = 'metadata_fields'
        else:
            config['ckan.plugins'] += ' metadata_fields'
        app = make_app(config['global_conf'], **config)
        app = webtest.TestApp(app)
        
        p.load('metadata_fields')
        
        cls.app = app;
    
    @classmethod
    def teardown_class(cls):
        model.Session.remove()
        model.repo.rebuild_db()
        p.unload('metadata_fields')
        pl._default_package_plugin = cls.original_default_package_plugin
        
    def test_list_of_all_groups(self):
        #app     = self._get_app()
        ctd.CreateTestData.create_groups([{'name':'test-group'}])
        plugin_exists   = False
        metadataPlugin  = None
        for plugin in p.PluginImplementations(p.ITemplateHelpers):
            if plugin.name == 'metadata_fields':
                plugin_exists   = True
                metadataPlugin  = plugin 
        
        assert plugin_exists is True, 'plugin metadata is not implementing ITemplateHelpers'
                
            
        groups  = plugin.get_helpers()['list_of_all_groups']();
        assert len(groups) > 0 , 'No groups in test data, that is not possible'
        assert not isinstance(groups[0], str), 'the function should not just return a list of group names'
        
        test_group_list = [g for g in groups if g['name']=='test-group']
        assert len(test_group_list)==1, 'Exactly one test-group group should be in the list'
        
    def test_cannot_create_dataset_wo_source(self):
        p.load('metadata_fields')
        testsysadmin = model.User.by_name('testsysadmin')
        result = tests.call_action_api(self.app, 'package_create', name='test-dataset',
                private=False, package_creator='test-creator',
                apikey=testsysadmin.apikey, status=409)

#         result = tk.get_action('package_create')({'user':'testsysadmin'},{'name': 'test-dataset', 'private':False})
        
        assert 'dataset_source' in result, 'The error needs to be related to the source'
        assert 'Missing value' in result['dataset_source'], 'The problem needs to be that the source info is missing'        
        