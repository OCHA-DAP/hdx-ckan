import ckan.tests.factories as factories

import ckan.plugins.toolkit as tk
import ckanext.hdx_theme.helpers.helpers as hdx_helpers

import ckanext.hdx_package.helpers.caching as caching
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

num_cached_group_list_called = 0
original_get_action = tk.get_action

num_filter_focus_countries = 0
original_filter_focus_countries = caching.filter_focus_countries

num_invalidate_group_caches = 0
original_invalidate_group_caches = caching.invalidate_group_caches


def get_action_wrapper(func):
    def my_get_action(action_name):
        global num_cached_group_list_called
        if action_name == 'group_list':
            num_cached_group_list_called += 1
        return func(action_name)

    return my_get_action


def filter_focus_countries_wrapper(func):
    def my_filter_focus_countries(*args, **kw):
        global num_filter_focus_countries
        num_filter_focus_countries += 1
        return func(*args, **kw)

    return my_filter_focus_countries


def invalidate_group_caches_wrapper(func):
    def my_invalidate_group_caches(*args, **kw):
        global num_invalidate_group_caches
        num_invalidate_group_caches += 1
        return func(*args, **kw)

    return my_invalidate_group_caches


class TestLocationOrder(hdx_test_base.HdxBaseTest):
    @classmethod
    def setup_class(cls):
        super(TestLocationOrder, cls).setup_class()

        factories.Group(name='world')

        global num_cached_group_list_called
        global num_filter_focus_countries

        tk.get_action = get_action_wrapper(tk.get_action)

        caching.filter_focus_countries = filter_focus_countries_wrapper(caching.filter_focus_countries)

        caching.invalidate_group_caches = invalidate_group_caches_wrapper(caching.invalidate_group_caches)

    @classmethod
    def teardown_class(cls):
        super(TestLocationOrder, cls).teardown_class()

        tk.get_action = original_get_action
        caching.filter_focus_countries = original_filter_focus_countries
        caching.invalidate_group_caches = original_invalidate_group_caches

    def test_cached_locations_list(self):
        global num_cached_group_list_called

        # calling the function to make sure it's cached
        locations_list = tk.get_action('cached_group_list')()

        # check if world is defined
        world_exists = False
        for location in locations_list:
            if location['name'] == 'world':
                world_exists = True
                break

        assert world_exists, 'world should be in locations_list, but wasn\'t found'

        # check if world is the first entry
        locations_list = hdx_helpers.hdx_location_list()

        assert locations_list and locations_list[0][
            'value'] == 'world', 'world should be the first entry in hdx_locations_list'
