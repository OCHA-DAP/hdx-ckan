'''
Created on Jun 16, 2014

@author: alexandru-m-g
'''

import ckan.lib.create_test_data as ctd
import ckan.config as ckanconfig
import webtest
import ckan.model as model
import ckan.lib.search as search

import ckan.new_tests.helpers as helpers

from pylons import config


def _get_test_app():
    config['ckan.legacy_templates'] = False
    app = ckanconfig.middleware.make_app(config['global_conf'], **config)
    app = webtest.TestApp(app)
    return app


def _load_plugin(plugin):
    plugins = set(config['ckan.plugins'].strip().split())
    plugins.add(plugin.strip())
    config['ckan.plugins'] = ' '.join(plugins)


class HdxBaseTest(object):

    @classmethod
    def _create_test_data(cls):
        ctd.CreateTestData.create()

    @classmethod
    def _load_plugins(cls):
        _load_plugin('hdx_theme')

    @classmethod
    def setup_class(cls):
        cls.original_config = config.copy()

        cls._load_plugins()
        cls.app = _get_test_app()

        search.clear()
        helpers.reset_db()
        cls._create_test_data()

    @classmethod
    def teardown_class(cls):
        model.Session.remove()
        model.repo.rebuild_db()

        config.clear()
        config.update(cls.original_config)
