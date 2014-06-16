'''
Created on Jun 3, 2014

@author: alexandru-m-g
'''

import ckan.plugins.toolkit as tk
import ckan.lib.create_test_data as ctd
import ckan.tests as tests
import ckan.lib.search as search
import ckan.model as model
import ckan.plugins as p

import ckanext.hdx_theme.caching as caching
import ckanext.hdx_theme.plugin as plugin

num_cached_group_list_called = 0
original_get_action = tk.get_action

num_filter_focus_countries = 0
original_filter_focus_countries = caching.filter_focus_countries

num_invalidate_group_caches = 0
original_invalidate_group_caches = caching.invalidate_group_caches

def get_action_wrapper(func):
    def my_get_action(action_name):
        global num_cached_group_list_called
        if action_name=='group_list':
            num_cached_group_list_called += 1
        return func(action_name)
    
    return my_get_action

def filter_focus_countries_wrapper(func):
    def my_filter_focus_countries(*args, **kw):
        global num_filter_focus_countries
        num_filter_focus_countries += 1
        return func(*args, **kw)
    
    return my_filter_focus_countries;

def invalidate_group_caches_wrapper(func):
    def my_invalidate_group_caches(*args, **kw):
        global num_invalidate_group_caches
        num_invalidate_group_caches += 1
        return func(*args, **kw)
    return my_invalidate_group_caches

class TestGroupsCaching(tests.WsgiAppCase):
    
    @classmethod
    def setup_class(cls):
        global num_cached_group_list_called
        global num_filter_focus_countries
        
        p.load('hdx_theme')
        
        search.clear()
        model.Session.remove()
        ctd.CreateTestData.create()
        
        tk.get_action   = get_action_wrapper(tk.get_action)
        
        caching.filter_focus_countries = filter_focus_countries_wrapper(caching.filter_focus_countries)
        
        caching.invalidate_group_caches = invalidate_group_caches_wrapper(caching.invalidate_group_caches)
   
    @classmethod
    def teardown_class(cls):
        model.Session.remove()
        model.repo.rebuild_db()
        
        tk.get_action   = original_get_action
        caching.filter_focus_countries = original_filter_focus_countries
        caching.invalidate_group_caches = original_invalidate_group_caches
        
        p.unload('hdx_theme')
        
    
    def test_cached_group_list(self):
        global num_cached_group_list_called
        
        # calling the function to make sure it's cached
        tk.get_action('cached_group_list')()
        # resetting counter
        num_cached_group_list_called = 0
        
        #the result should have been cached so group_list should not be called
        tk.get_action('cached_group_list')()
        assert num_cached_group_list_called == 0, \
            'number of calls to group_list should be 0 , instead {num}'.format(num=num_cached_group_list_called)
        
        caching.invalidate_group_caches()
        #the result should have been removed from cache so group_list should be called
        tk.get_action('cached_group_list')()
        assert num_cached_group_list_called == 1, \
            'number of calls to group_list should be 1 , instead {num}'.format(num=num_cached_group_list_called)
        
        #the result should have been cached so the number of calls to group_list shouldn't increase
        tk.get_action('cached_group_list')()
        assert num_cached_group_list_called == 1, \
            'number of calls to group_list should be 1 , instead {num}'.format(num=num_cached_group_list_called)
            
    def test_cached_get_group_package_stuff(self):
        global num_filter_focus_countries
        
        # calling the function to make sure it's cached
        caching.cached_get_group_package_stuff()
         # resetting counter
        num_filter_focus_countries = 0
        
        #the result should have been cached so filter_focus_countries should not be called
        caching.cached_get_group_package_stuff()
        assert num_filter_focus_countries == 0, \
            'number of calls to filter_focus_countries should be 0 , instead {num}'.format(num=num_filter_focus_countries)
            
        caching.invalidate_group_caches()
        #the result should have been removed from cache so filter_focus_countries should be called
        caching.cached_get_group_package_stuff()
        assert num_filter_focus_countries == 1, \
            'number of calls to filter_focus_countries should be 1 , instead {num}'.format(num=num_filter_focus_countries)
            
        #the result should have been cached so the num of calls to filter_focus_countries shouldn't increase
        caching.cached_get_group_package_stuff()
        assert num_filter_focus_countries == 1, \
            'number of calls to filter_focus_countries should be 1 , instead {num}'.format(num=num_filter_focus_countries)
            
    def test_group_cache_invalidation_on_change(self):
        global num_invalidate_group_caches
        # resetting counter
        num_invalidate_group_caches = 0
        
        testsysadmin = model.User.by_name('testsysadmin')
        result = tests.call_action_api(self.app, 'group_create', name='group_test',
                apikey=testsysadmin.apikey, status=200)
        
        assert num_invalidate_group_caches == 1, \
            'on group_create cache invalidation should have been called'
        
        
