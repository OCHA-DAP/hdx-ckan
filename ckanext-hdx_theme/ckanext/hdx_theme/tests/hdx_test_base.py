'''
Created on Jun 16, 2014

@author: alexandru-m-g
'''

import webtest
import logging
import ckan.lib.create_test_data as ctd
import ckan.config as ckanconfig
import ckan.model as model
import ckan.lib.search as search
import ckan.logic as logic

import ckan.new_tests.helpers as helpers

import ckanext.hdx_package.helpers.helpers as hdx_actions

from pylons import config


log = logging.getLogger(__name__)

original_package_create = hdx_actions.package_create


def _get_test_app():
    config['ckan.legacy_templates'] = False
    app = ckanconfig.middleware.make_app(config['global_conf'], **config)
    app = webtest.TestApp(app)
    return app


def load_plugin(plugin):
    plugins = set(config['ckan.plugins'].strip().split())
    plugins.update(plugin.strip().split())
    config['ckan.plugins'] = ' '.join(plugins)


class HdxBaseTest(object):
    '''
    NOTE: Since more fields have been made mandatory for a dataset the process of creating test
    data at the beginning of a test suit was failing.
    Therefore the package_create action is now wrapped while running the tests to automatically
    populate some missing fields.
    See replace_package_create ()
    '''

    @classmethod
    def _create_test_data(cls):
        ctd.CreateTestData.create()

    @classmethod
    def _load_plugins(cls):
        load_plugin('hdx_theme')

    @classmethod
    def setup_class(cls):
        cls.original_config = config.copy()

        cls._load_plugins()
        cls.app = _get_test_app()

        search.clear()
        helpers.reset_db()

        cls.replace_package_create()

        cls._create_test_data()

    @classmethod
    def teardown_class(cls):
        model.Session.remove()
        model.repo.rebuild_db()

        config.clear()
        config.update(cls.original_config)
        logic._actions['package_create'] = original_package_create

    @classmethod
    def replace_package_create(cls):
        '''
        overrride this with an empty function in your class if you want the original
        package_create function that does not automatically populate some of the mandatory
        fields. ( More info in the class description )
        '''
        def package_create_wrapper(context, data_dict):
            if not data_dict.get('license_id'):
                data_dict['license_id'] = 'cc'

            private = False if str(data_dict.get('private','')).lower() == 'false' else True
            if not private:
                if not data_dict.get('data_update_frequency'):
                    data_dict['data_update_frequency'] = '0'
                if not data_dict.get('dataset_date'):
                    data_dict['dataset_date'] = '11/11/2011'
                if not data_dict.get('methodology'):
                    data_dict['methodology'] = 'Automatically inserted test methodology'
            return original_package_create(context, data_dict)
        logic._actions['package_create'] = package_create_wrapper


class HdxFunctionalBaseTest(HdxBaseTest):

    '''A base class for functional testing that loads all hdx_* extensions.'''

    @classmethod
    def _load_plugins(cls):
        load_plugin('hdx_service_checker hdx_crisis hdx_search sitemap hdx_org_group hdx_group hdx_package hdx_user_extra hdx_mail_validate hdx_users hdx_theme')
