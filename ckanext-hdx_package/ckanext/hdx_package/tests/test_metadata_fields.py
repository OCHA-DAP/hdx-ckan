'''
Created on May 16, 2014

@author: alexandru-m-g

'''

import ckan.tests as tests
import webtest
import ckan.plugins as p
import ckan.lib.create_test_data as ctd
import ckan.lib.search as search
import ckan.model as model
import ckan.logic as logic
import ckan.lib.helpers as h
import logging
import requests

from ckan.config.middleware import make_app
from pylons import config

import ckanext.hdx_package.helpers.caching as caching

log = logging.getLogger(__name__)

class TestMetadataFields(tests.WsgiAppCase):
    
    @classmethod
    def setup_class(cls):
#         p.load('metadata_fields')
#         TestMetadataFields.get_app()
        search.clear()
        model.Session.remove()
        ctd.CreateTestData.create()
        # Need to invalidate the caches to make sure the new data is being served
        caching.invalidate_group_caches()
        
      
    @classmethod
    def get_app(cls):
        '''
        Alternative method for creating a test app. Not needed if inheriting from WsgiAppCase
        '''
        if not 'ckan.plugins' in config:
            config['ckan.plugins'] = 'hdx_package'
        else:
            config['ckan.plugins'] += 'hdx_package'
        app = make_app(config['global_conf'], **config)
        app = webtest.TestApp(app)
        
#       p.load('metadata_fields')
        
        cls.app = app;
    
    @classmethod
    def teardown_class(cls):
        model.Session.remove()
        model.repo.rebuild_db()
        p.unload('hdx_package')
    
    #ASK ALEX ABOUT THIS ONE    
    # def test_list_of_all_groups(self):
    #     #app     = self._get_app()
    #     ctd.CreateTestData.create_groups([{'name':'test-group'}])
    #     plugin_exists   = False
    #     metadataPlugin  = None
    #     for plugin in p.PluginImplementations(p.ITemplateHelpers):
    #         if plugin.name == 'hdx_package':
    #             plugin_exists   = True
    #             metadataPlugin  = plugin 
        
    #     assert plugin_exists is True, 'plugin metadata is not implementing ITemplateHelpers'
                
            
    #     groups  = metadataPlugin.get_helpers()['list_of_all_groups']();
    #     assert len(groups) > 0 , 'No groups in test data, that is not possible'
    #     assert not isinstance(groups[0], str), 'the function should not just return a list of group names'
        
    #     test_group_list = [g for g in groups if g['name']=='test-group']
    #     assert len(test_group_list)==1, 'Exactly one test-group group should be in the list'
        
    def test_cannot_create_dataset_wo_source(self):
        try:
            p.load('hdx_package')
        except Exception as e:
            log.warn('Module already loaded')
            log.info(str(e))
            
        testsysadmin = model.User.by_name('testsysadmin')
        result = tests.call_action_api(self.app, 'package_create', name='test-dataset',
                private=False, package_creator='test-creator',
                apikey=testsysadmin.apikey, status=409)

#         result = tk.get_action('package_create')({'user':'testsysadmin'},{'name': 'test-dataset', 'private':False})
        
        assert 'dataset_source' in result, 'The error needs to be related to the source'
        assert 'Missing value' in result['dataset_source'], 'The problem needs to be that the source info is missing'


    def test_private_is_private(self):
        try:
            p.load('hdx_package')
        except Exception as e:
            log.warn('Module already loaded')
            log.info(str(e))
    
        tester = model.User.by_name('tester')
        tests.call_action_api(self.app, 'organization_create',
                                        name='test_org_2',
                                        apikey=tester.apikey)

        tests.call_action_api(self.app, 'package_create', name='test-dataset-private',
                private=True, owner_org='test_org_2',package_creator='test-creator', dataset_source='test',
                resources=[{'url':'text_upload_file.txt'}], apikey=tester.apikey, status=409)
        ds = tests.call_action_api(self.app, 'package_show', id='test-dataset-private', apikey=tester.apikey, status=409)
        r =  requests.get(ds['resources'][0]['url'])
        assert r.text == 'Hello World'

    def test_related_items_owner_status(self):
        #after edit of a related item the owner id is unchanged

        #create related item
        offset = h.url_for(controller='related',
                           action='new', id='warandpeace')
        data = {
            "title": "testing_create",
            "url": u"http://ckan.org/feed/",
        }
        user = model.User.by_name('tester')
        admin = model.User.by_name('testsysadmin')

        context = dict(model=model, user=user.name, session=model.Session)
        data_dict = dict(title="testing_create",description="description",
                         url="http://ckan.org/feed/",image_url="",type="visualization")
        res = logic.get_action("related_create")( context, data_dict )

        #edit related item
        data_dict = dict(id=res['id'],title="testing_update",description="description",
                         url="http://ckan.org/feed/",image_url="",type="visualization")

        context = dict(model=model, user='testsysadmin', session=model.Session)
        result = logic.get_action('related_update')(context,data_dict)
        #Confirm related item owner status
        assert result['owner_id'] == user.id

    def _related_create(self, title, description, type, url, image_url):
        usr = logic.get_action('get_site_user')({'model':model,'ignore_auth': True},{})

        context = dict(model=model, user=usr['name'], session=model.Session)
        data_dict = dict(title=title,description=description,
                         url=url,image_url=image_url,type=type)
        return logic.get_action("related_create")( context, data_dict )